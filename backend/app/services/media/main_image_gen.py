"""
商品主图生成编排器

根据商品信息生成电商5张主图：白底图、场景图、细节图、卖点图、模特图。
路由策略：白底/细节 -> 万相(便宜)，场景/卖点 -> 即梦(创意)
"""

import asyncio
import logging

from app.services.media.image_gen import generate_image, generate_batch

logger = logging.getLogger("shangtanai.media.main_image")

STYLE_PROMPTS = {
    "white_bg": {
        "template": (
            "电商商品主图，{product}，纯白色背景，正面展示，"
            "高清产品摄影，无人物，专业灯光，淘宝主图风格"
        ),
        "negative": "文字、水印、人物、杂物、阴影过重",
        "size": "800*800",
    },
    "scene": {
        "template": (
            "商品场景图，{product}，真实使用场景，"
            "自然光线，生活感氛围，高清摄影"
        ),
        "negative": "纯白背景、文字、水印、卡通",
        "size": "800*800",
    },
    "detail": {
        "template": (
            "商品细节特写，{product}，微距摄影，"
            "展示材质和工艺细节，高清纹理"
        ),
        "negative": "远景、全身照、模糊、文字",
        "size": "800*800",
    },
    "selling_point": {
        "template": (
            "电商卖点图，{product}，突出核心卖点，"
            "简洁构图，吸引力强，商业广告风格"
        ),
        "negative": "杂乱、低质量、模糊",
        "size": "800*800",
    },
    "model": {
        "template": (
            "电商模特展示图，{product}，模特手持或穿戴展示，"
            "不露脸，自然姿态，白色背景，商业摄影"
        ),
        "negative": "变形、模糊、卡通、正面露脸",
        "size": "800*800",
    },
}


async def generate_main_images(
    product_info: str,
    styles: list[str] | None = None,
    model_asset_id: str | None = None,
    size: str = "800*800",
    source_images: list[str] | None = None,
    prompt_package: dict | None = None,
) -> list[dict]:
    """
    Generate product main images for e-commerce listing.

    Args:
        product_info: product name and description text
        styles: list of style keys, defaults to 4 standard styles
        model_asset_id: optional saved virtual model asset ID
        size: output image size, default "800*800"
        source_images: optional list of local image paths for reference
        prompt_package: optional dict with main_image_prompts from SceneArchitect

    Returns:
        [{"style": "white_bg", "images": [...], "cost": 0.04}, ...]
    """
    if styles is None:
        styles = ["white_bg", "scene", "detail", "selling_point"]

    # Extract product keywords for better prompts
    product_short = product_info[:50]

    # Determine ref image for generate_image calls
    ref_image_path = source_images[0] if source_images else None

    # If prompt_package has main_image_prompts, use those instead of templates
    ai_prompts = {}
    if prompt_package and prompt_package.get("main_image_prompts"):
        for item in prompt_package["main_image_prompts"]:
            style_key = item.get("style")
            if style_key:
                ai_prompts[style_key] = item

    prompts = []
    for style in styles:
        if style in ai_prompts:
            # Use AI-generated prompt from SceneArchitect
            ai_item = ai_prompts[style]
            prompts.append({
                "prompt": ai_item.get("prompt", ""),
                "negative_prompt": ai_item.get("negative_prompt", ""),
                "style": style,
            })
        else:
            # Fallback to template-based prompts
            cfg = STYLE_PROMPTS.get(style)
            if not cfg:
                logger.warning(f"Unknown style '{style}', skipping")
                continue
            prompt_text = cfg["template"].format(product=product_short)
            prompts.append({
                "prompt": prompt_text,
                "negative_prompt": cfg["negative"],
                "style": style,
            })

    if not prompts:
        return []

    # Generate images sequentially to avoid API rate limiting (429)
    results = []
    for i, p in enumerate(prompts):
        if i > 0:
            await asyncio.sleep(2)  # 间隔2秒避免限流
        try:
            r = await generate_image(
                prompt=p["prompt"],
                negative_prompt=p["negative_prompt"],
                size=size,
                n=1,
                ref_image_path=ref_image_path,
            )
            results.append(r)
        except Exception as e:
            logger.warning(f"Main image '{p['style']}' failed: {e}")
            results.append(e)

    output = []
    for p, r in zip(prompts, results):
        if isinstance(r, Exception):
            logger.warning(f"Main image '{p['style']}' failed: {r}")
            output.append({"style": p["style"], "images": [], "cost": 0})
        else:
            cost = sum(img.get("cost", 0) for img in r)
            output.append({"style": p["style"], "images": r, "cost": cost})

    total = sum(o["cost"] for o in output)
    logger.info(f"Generated {len(styles)} main images, total cost: {total:.2f} CNY")
    return output
