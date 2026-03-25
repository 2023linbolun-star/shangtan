"""
小红书图文排版合成服务

使用 Pillow 将 AI 生成的图片 + 文字排版合成小红书风格组图。
输出：封面图(1张) + 内容图(5张) = 6张发布包

功能：
- 封面图：产品图 + 标题文字叠加
- 内容图：场景图 + 要点文字卡片
- 统一色调滤镜
- 小红书风格排版（圆角、阴影、间距）
"""

import logging
import os
import uuid
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from app.services.experts.video_specs import XHS_IMAGE, SUBTITLE

logger = logging.getLogger("shangtanai.media.xhs_compose")

# 小红书视觉风格常量
XHS_STYLE = {
    "bg_color": "#F5F5F0",           # 米白背景
    "text_color": "#2C2C2C",         # 深灰文字
    "accent_color": "#FF4757",       # 小红书红
    "subtitle_color": "#666666",     # 副文字颜色
    "corner_radius": 24,             # 圆角
    "padding": 60,                   # 内边距
    "shadow_offset": (4, 4),
    "shadow_blur": 10,
}


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """加载中文字体。"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",                    # macOS
        "/System/Library/Fonts/STHeiti Light.ttc",               # macOS备选
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    logger.warning("No CJK font found, using default")
    return ImageFont.load_default()


def _add_rounded_corners(img: Image.Image, radius: int) -> Image.Image:
    """为图片添加圆角。"""
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    result = img.copy()
    result.putalpha(mask)
    return result


def _apply_xhs_filter(img: Image.Image) -> Image.Image:
    """应用小红书风格滤镜（轻微提亮+降饱和+暖色调）。"""
    # 轻微提亮
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)
    # 轻微降饱和（高级感）
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.9)
    # 轻微提高对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.05)
    return img


def compose_cover(
    product_image_path: str,
    title: str,
    subtitle: str = "",
    output_path: str | None = None,
) -> str:
    """
    合成小红书封面图：产品图 + 标题文字叠加。

    Args:
        product_image_path: 产品/场景图路径
        title: 主标题
        subtitle: 副标题
        output_path: 输出路径

    Returns:
        输出文件路径
    """
    w, h = XHS_IMAGE["cover_size"]
    canvas = Image.new("RGB", (w, h), XHS_STYLE["bg_color"])
    draw = ImageDraw.Draw(canvas)

    # 加载产品图
    if product_image_path and os.path.exists(product_image_path):
        product_img = Image.open(product_image_path).convert("RGB")
        product_img = _apply_xhs_filter(product_img)

        # 产品图占画面上方70%
        img_area_h = int(h * 0.7)
        product_img = _fit_image(product_img, w, img_area_h)
        canvas.paste(product_img, (0, 0))

    # 底部文字区域（半透明白底）
    text_area_top = int(h * 0.68)
    text_bg = Image.new("RGBA", (w, h - text_area_top), (255, 255, 255, 230))
    canvas.paste(Image.new("RGB", (w, h - text_area_top), "#FFFFFF"), (0, text_area_top))

    # 标题
    title_font = _get_font(52, bold=True)
    padding = XHS_STYLE["padding"]
    _draw_text_wrapped(
        draw, title, title_font,
        xy=(padding, text_area_top + 30),
        max_width=w - padding * 2,
        fill=XHS_STYLE["text_color"],
        line_spacing=12,
    )

    # 副标题
    if subtitle:
        subtitle_font = _get_font(30)
        _draw_text_wrapped(
            draw, subtitle, subtitle_font,
            xy=(padding, text_area_top + 140),
            max_width=w - padding * 2,
            fill=XHS_STYLE["subtitle_color"],
        )

    output_path = output_path or f"storage/assets/xhs/{uuid.uuid4().hex[:8]}/cover.jpg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, "JPEG", quality=XHS_IMAGE["quality"])
    logger.info(f"Cover composed: {output_path}")
    return output_path


def compose_content_card(
    background_image_path: str,
    headline: str,
    body_text: str,
    text_overlay: str = "",
    card_number: int = 1,
    output_path: str | None = None,
) -> str:
    """
    合成小红书内容图：场景图背景 + 文字卡片。

    Args:
        background_image_path: 背景图路径
        headline: 卡片标题
        body_text: 卡片正文
        text_overlay: 直接叠加在图片上的文字
        card_number: 第几张图
        output_path: 输出路径
    """
    w, h = XHS_IMAGE["body_size"]
    canvas = Image.new("RGB", (w, h), XHS_STYLE["bg_color"])
    draw = ImageDraw.Draw(canvas)

    # 背景图
    if background_image_path and os.path.exists(background_image_path):
        bg_img = Image.open(background_image_path).convert("RGB")
        bg_img = _apply_xhs_filter(bg_img)
        bg_img = _fit_image(bg_img, w, h)
        canvas.paste(bg_img, (0, 0))

    # 图片直接叠加文字（如有）
    if text_overlay:
        overlay_font = _get_font(44, bold=True)
        _draw_text_with_shadow(
            draw, text_overlay, overlay_font,
            xy=(XHS_STYLE["padding"], int(h * 0.08)),
            fill="#FFFFFF",
            shadow_color="#00000088",
        )

    # 底部文字卡片（半透明白底圆角卡片）
    card_h = int(h * 0.35)
    card_top = h - card_h - 40
    card_margin = 40

    # 画圆角白底卡片
    card_img = Image.new("RGBA", (w - card_margin * 2, card_h), (255, 255, 255, 230))
    card_img = _add_rounded_corners(card_img, XHS_STYLE["corner_radius"])

    # 粘贴卡片（需要处理透明通道）
    temp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    temp.paste(card_img, (card_margin, card_top), card_img)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), temp).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # 卡片内文字
    inner_padding = card_margin + 30
    headline_font = _get_font(36, bold=True)
    body_font = _get_font(26)

    # 标题
    draw.text(
        (inner_padding, card_top + 30),
        headline,
        font=headline_font,
        fill=XHS_STYLE["text_color"],
    )

    # 正文
    _draw_text_wrapped(
        draw, body_text, body_font,
        xy=(inner_padding, card_top + 85),
        max_width=w - inner_padding * 2,
        fill=XHS_STYLE["subtitle_color"],
        line_spacing=10,
        max_lines=6,
    )

    output_path = output_path or f"storage/assets/xhs/{uuid.uuid4().hex[:8]}/card_{card_number}.jpg"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, "JPEG", quality=XHS_IMAGE["quality"])
    logger.info(f"Content card {card_number} composed: {output_path}")
    return output_path


def compose_full_set(
    image_paths: list[str],
    image_texts: list[dict],
    title: str,
    output_dir: str | None = None,
) -> list[str]:
    """
    合成完整的小红书图文发布包（6张图）。

    Args:
        image_paths: AI生成的图片路径列表（至少6张）
        image_texts: 每张图的文字信息
            [{"headline": "...", "body": "...", "text_overlay": "..."}, ...]
        title: 笔记标题（封面用）
        output_dir: 输出目录

    Returns:
        输出文件路径列表
    """
    output_dir = output_dir or os.path.join("storage/assets/xhs", str(uuid.uuid4())[:8])
    os.makedirs(output_dir, exist_ok=True)

    results = []

    # 封面图
    cover_path = os.path.join(output_dir, "01_cover.jpg")
    cover_subtitle = image_texts[0].get("body", "") if image_texts else ""
    compose_cover(
        product_image_path=image_paths[0] if image_paths else "",
        title=title,
        subtitle=cover_subtitle[:50],
        output_path=cover_path,
    )
    results.append(cover_path)

    # 内容图（图2-图6）
    for i in range(1, min(6, len(image_paths))):
        card_path = os.path.join(output_dir, f"{i+1:02d}_card.jpg")
        text_info = image_texts[i] if i < len(image_texts) else {}

        compose_content_card(
            background_image_path=image_paths[i],
            headline=text_info.get("headline", ""),
            body_text=text_info.get("body", ""),
            text_overlay=text_info.get("text_overlay", ""),
            card_number=i + 1,
            output_path=card_path,
        )
        results.append(card_path)

    logger.info(f"XHS full set composed: {len(results)} images → {output_dir}")
    return results


# ── 工具函数 ──

def _fit_image(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """等比缩放并居中裁切到目标尺寸。"""
    ratio_w = target_w / img.width
    ratio_h = target_h / img.height
    ratio = max(ratio_w, ratio_h)

    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 居中裁切
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _draw_text_wrapped(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    xy: tuple,
    max_width: int,
    fill: str,
    line_spacing: int = 8,
    max_lines: int = 10,
):
    """自动换行绘制文字。"""
    x, y = xy
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line

    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines[:max_lines]):
        bbox = font.getbbox(line)
        line_height = bbox[3] - bbox[1]
        draw.text((x, y + i * (line_height + line_spacing)), line, font=font, fill=fill)


def _draw_text_with_shadow(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    xy: tuple,
    fill: str,
    shadow_color: str = "#00000088",
):
    """带阴影的文字绘制。"""
    x, y = xy
    offset = XHS_STYLE["shadow_offset"]
    draw.text((x + offset[0], y + offset[1]), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=fill)
