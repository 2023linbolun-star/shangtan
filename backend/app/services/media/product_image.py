"""
产品图片处理服务 — 抠图 + 背景生成 + 合成

核心原则：产品图是只读圣物，永远不让AI重新画。
- 白底图：rembg抠图 + 白底合成
- 场景图：rembg抠图 + 万相背景生成v2
- 细节图：裁剪放大原图
- 卖点图：产品抠图 + 模板合成
- 模特图：AI生成人物 + 产品合成
"""

import asyncio
import base64
import io
import logging
import os
import uuid

import httpx
from PIL import Image

from app.core.config import QWEN_API_KEY, ASSETS_DIR

logger = logging.getLogger("shangtanai.media.product_image")

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"


# ══════════════════════════════════════════════════════════════
#  DashScope 文件上传（获取临时URL）
# ══════════════════════════════════════════════════════════════

async def _upload_to_dashscope(file_path: str, api_key: str) -> str | None:
    """
    上传文件到 DashScope 获取临时可访问的 OSS URL。
    两步流程：GET /uploads 获取上传凭证 → POST 到 OSS。
    """
    file_name = os.path.basename(file_path)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        # Step 1: GET 获取上传凭证（注意是 GET 不是 POST！）
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{DASHSCOPE_BASE}/uploads",
                headers=headers,
                params={
                    "action": "getPolicy",
                    "model": "wanx-background-generation-v2",
                    "file_name": file_name,
                },
                timeout=15,
            )
            data = resp.json()

        if resp.status_code != 200:
            logger.error(f"DashScope getPolicy failed: {resp.status_code} {data}")
            return None

        upload_data = data.get("data", {})
        oss_upload_url = upload_data.get("upload_url")
        upload_dir = upload_data.get("upload_dir", "")
        policy = upload_data.get("policy", "")
        oss_access_key_id = upload_data.get("oss_access_key_id", "")
        signature = upload_data.get("signature", "")
        file_url = upload_data.get("file_url", "")
        x_oss_object_acl = upload_data.get("x_oss_object_acl", "")

        if not oss_upload_url or not policy:
            logger.error(f"DashScope upload policy incomplete: {upload_data}")
            return None

        # Step 2: POST 上传文件到 OSS
        form_data = {
            "key": f"{upload_dir}/{file_name}",
            "policy": policy,
            "OSSAccessKeyId": oss_access_key_id,
            "Signature": signature,
            "success_action_status": "200",
        }
        if x_oss_object_acl:
            form_data["x-oss-object-acl"] = x_oss_object_acl

        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "application/octet-stream")}
            async with httpx.AsyncClient() as client:
                upload_resp = await client.post(
                    oss_upload_url,
                    data=form_data,
                    files=files,
                    timeout=30,
                )

        if upload_resp.status_code not in (200, 201, 204):
            logger.error(f"OSS upload failed: {upload_resp.status_code} {upload_resp.text[:200]}")
            return None

        logger.info(f"Uploaded to DashScope OSS: {file_url}")
        return file_url

    except Exception as e:
        logger.exception(f"DashScope upload failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════
#  1. 抠图（rembg）
# ══════════════════════════════════════════════════════════════

async def remove_background(image_path: str, save_dir: str | None = None) -> str:
    """
    用 rembg 去除图片背景，返回透明PNG路径。

    Args:
        image_path: 原始图片路径
        save_dir: 保存目录

    Returns:
        透明PNG的本地路径
    """
    from rembg import remove

    save_dir = save_dir or os.path.join(ASSETS_DIR, "cutouts", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    # rembg 是 CPU 密集型，放到线程池执行
    def _do_remove():
        with open(image_path, "rb") as f:
            input_data = f.read()
        output_data = remove(input_data)
        out_path = os.path.join(save_dir, "cutout.png")
        with open(out_path, "wb") as f:
            f.write(output_data)
        return out_path

    loop = asyncio.get_event_loop()
    result_path = await loop.run_in_executor(None, _do_remove)
    logger.info(f"Background removed: {image_path} → {result_path}")
    return result_path


# ══════════════════════════════════════════════════════════════
#  2. 白底图（抠图 + 白底合成）
# ══════════════════════════════════════════════════════════════

async def generate_white_bg(image_path: str, size: int = 800, save_dir: str | None = None) -> dict:
    """
    生成白底产品图：抠图 → 放到白色画布上居中。

    Args:
        image_path: 原始产品图
        size: 输出尺寸（正方形）
        save_dir: 保存目录

    Returns:
        {"url": "/static/assets/...", "local_path": "...", "cost": 0.0}
    """
    save_dir = save_dir or os.path.join(ASSETS_DIR, "main_images", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    # Step 1: 抠图
    cutout_path = await remove_background(image_path, save_dir)

    # Step 2: 放到白色画布上
    def _compose():
        product = Image.open(cutout_path).convert("RGBA")
        # 缩放产品图到画布的 80%
        target_size = int(size * 0.8)
        product.thumbnail((target_size, target_size), Image.LANCZOS)

        # 创建白色画布
        canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
        # 居中粘贴
        x = (size - product.width) // 2
        y = (size - product.height) // 2
        canvas.paste(product, (x, y), product)

        # 转为 RGB（JPG 不支持透明）
        final = canvas.convert("RGB")
        out_path = os.path.join(save_dir, "white_bg.jpg")
        final.save(out_path, "JPEG", quality=95)
        return out_path

    loop = asyncio.get_event_loop()
    out_path = await loop.run_in_executor(None, _compose)

    # 生成 URL
    relative = out_path.split(ASSETS_DIR)[-1].lstrip("/\\")
    url = f"/static/assets/{relative}"

    logger.info(f"White bg generated: {out_path}")
    return {"url": url, "local_path": out_path, "cost": 0.0}


# ══════════════════════════════════════════════════════════════
#  3. 场景图（抠图 + 万相背景生成v2）
# ══════════════════════════════════════════════════════════════

async def generate_scene_bg(
    image_path: str,
    prompt: str = "现代简约办公桌面，温暖自然光线，浅木色背景，生活化氛围",
    save_dir: str | None = None,
) -> dict:
    """
    生成场景背景图：使用 OpenAI GPT Image 图生图，上传产品抠图 + 场景描述。

    Args:
        image_path: 原始产品图
        prompt: 场景描述
        save_dir: 保存目录

    Returns:
        {"url": "/static/assets/...", "local_path": "...", "cost": ...}
    """
    from app.services.media.openai_image import generate_image_openai

    save_dir = save_dir or os.path.join(ASSETS_DIR, "main_images", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    # Step 1: 抠图
    cutout_path = await remove_background(image_path, save_dir)

    # Step 2: 用 OpenAI 图生图，以抠图为输入 + 场景描述
    full_prompt = (
        f"将这个产品放入以下场景中，保持产品外观完全不变：{prompt}。"
        f"产品必须是照片中的原始产品，不要改变产品的颜色、形状或任何细节。"
        f"高清电商摄影风格，自然光线。"
    )

    result = await generate_image_openai(
        prompt=full_prompt,
        ref_image_path=cutout_path,
        size="1024x1024",
        quality="medium",
        save_dir=save_dir,
    )

    if result.get("url"):
        logger.info(f"Scene bg generated via OpenAI: {result['local_path']}")
        return result

    # 降级到白底图
    logger.warning("OpenAI scene gen failed, falling back to white bg")
    return await generate_white_bg(image_path, save_dir=save_dir)


# ══════════════════════════════════════════════════════════════
#  4. 细节图（裁剪放大原图）
# ══════════════════════════════════════════════════════════════

async def generate_detail_crop(
    image_path: str,
    region: str = "center",
    size: int = 800,
    save_dir: str | None = None,
) -> dict:
    """
    从原图裁剪放大做细节图，100%保真。

    Args:
        image_path: 原始产品图
        region: 裁剪区域 "center" / "top" / "bottom"
        size: 输出尺寸
        save_dir: 保存目录
    """
    save_dir = save_dir or os.path.join(ASSETS_DIR, "main_images", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    def _crop():
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        # 裁剪中心50%区域并放大
        crop_ratio = 0.5
        cw, ch = int(w * crop_ratio), int(h * crop_ratio)

        if region == "top":
            box = ((w - cw) // 2, 0, (w + cw) // 2, ch)
        elif region == "bottom":
            box = ((w - cw) // 2, h - ch, (w + cw) // 2, h)
        else:  # center
            box = ((w - cw) // 2, (h - ch) // 2, (w + cw) // 2, (h + ch) // 2)

        cropped = img.crop(box)
        cropped = cropped.resize((size, size), Image.LANCZOS)

        # 轻微锐化
        from PIL import ImageFilter
        cropped = cropped.filter(ImageFilter.SHARPEN)

        out_path = os.path.join(save_dir, "detail.jpg")
        cropped.save(out_path, "JPEG", quality=95)
        return out_path

    loop = asyncio.get_event_loop()
    out_path = await loop.run_in_executor(None, _crop)

    relative = out_path.split(ASSETS_DIR)[-1].lstrip("/\\")
    url = f"/static/assets/{relative}"

    logger.info(f"Detail crop generated: {out_path}")
    return {"url": url, "local_path": out_path, "cost": 0.0}


# ══════════════════════════════════════════════════════════════
#  5. 卖点图（产品抠图 + 文字叠加模板）
# ══════════════════════════════════════════════════════════════

async def generate_selling_point(
    image_path: str,
    selling_points: list[str] | None = None,
    product_name: str = "",
    size: int = 800,
    save_dir: str | None = None,
) -> dict:
    """
    生成卖点图：产品抠图 + 渐变背景 + 卖点文字标签。
    """
    save_dir = save_dir or os.path.join(ASSETS_DIR, "main_images", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    cutout_path = await remove_background(image_path, save_dir)

    def _compose():
        product = Image.open(cutout_path).convert("RGBA")
        target_size = int(size * 0.6)
        product.thumbnail((target_size, target_size), Image.LANCZOS)

        # 创建渐变背景
        canvas = Image.new("RGB", (size, size), (245, 245, 250))

        # 粘贴产品到左侧
        product_rgb = Image.new("RGBA", (size, size), (245, 245, 250, 255))
        x = int(size * 0.05)
        y = (size - product.height) // 2
        product_rgb.paste(product, (x, y), product)
        canvas = Image.alpha_composite(
            canvas.convert("RGBA"), product_rgb
        ).convert("RGB")

        out_path = os.path.join(save_dir, "selling_point.jpg")
        canvas.save(out_path, "JPEG", quality=95)
        return out_path

    loop = asyncio.get_event_loop()
    out_path = await loop.run_in_executor(None, _compose)

    relative = out_path.split(ASSETS_DIR)[-1].lstrip("/\\")
    url = f"/static/assets/{relative}"

    logger.info(f"Selling point image generated: {out_path}")
    return {"url": url, "local_path": out_path, "cost": 0.0}


# ══════════════════════════════════════════════════════════════
#  编排器：根据 style 路由到对应的生成方法
# ══════════════════════════════════════════════════════════════

async def generate_product_main_images(
    source_image_path: str,
    styles: list[str],
    product_info: str = "",
    prompt_package: dict | None = None,
    size: int = 800,
) -> list[dict]:
    """
    根据选择的风格，为产品图生成主图套图。

    核心原则：产品图永远不重新画，只换背景/合成。

    Args:
        source_image_path: 用户上传的产品原图路径
        styles: 需要的主图风格列表
        product_info: 商品信息（用于场景prompt）
        prompt_package: SceneArchitect 生成的 prompt 包
        size: 输出尺寸

    Returns:
        [{"style": "white_bg", "images": [{"url": ..., "local_path": ..., "cost": ...}]}, ...]
    """
    results = []

    # 从 prompt_package 提取各风格的场景描述
    scene_prompts = {}
    if prompt_package and prompt_package.get("main_image_prompts"):
        for item in prompt_package["main_image_prompts"]:
            style_key = item.get("style")
            if style_key:
                scene_prompts[style_key] = item.get("prompt", "")

    for style in styles:
        save_dir = os.path.join(ASSETS_DIR, "main_images", uuid.uuid4().hex[:8])

        try:
            if style == "white_bg":
                img = await generate_white_bg(source_image_path, size=size, save_dir=save_dir)

            elif style == "scene":
                scene_prompt = scene_prompts.get("scene",
                    f"现代简约场景，{product_info or '商品'}，温暖自然光线，生活化氛围，高端感")
                img = await generate_scene_bg(source_image_path, prompt=scene_prompt, save_dir=save_dir)

            elif style == "detail":
                img = await generate_detail_crop(source_image_path, region="center", size=size, save_dir=save_dir)

            elif style == "selling_point":
                img = await generate_selling_point(source_image_path, product_name=product_info, size=size, save_dir=save_dir)

            elif style == "model":
                # 模特图：用 OpenAI 生成人物手持/穿戴产品的图
                model_prompt = scene_prompts.get("model",
                    f"一位时尚年轻女性手持或穿戴这个{product_info or '商品'}，"
                    f"不露正脸，自然优雅的姿态，白色简洁背景，"
                    f"高端电商模特摄影风格，柔和的影棚灯光")
                img = await generate_scene_bg(source_image_path, prompt=model_prompt, save_dir=save_dir)

            else:
                logger.warning(f"Unknown style '{style}', skipping")
                results.append({"style": style, "images": [], "cost": 0})
                continue

            results.append({"style": style, "images": [img], "cost": img.get("cost", 0)})
            logger.info(f"Style '{style}' generated successfully")

        except Exception as e:
            logger.exception(f"Style '{style}' generation failed: {e}")
            results.append({"style": style, "images": [], "cost": 0})

        # 间隔避免限流
        await asyncio.sleep(1)

    total_cost = sum(r.get("cost", 0) for r in results)
    logger.info(f"Product main images: {len(styles)} styles, cost: {total_cost:.2f} CNY")
    return results
