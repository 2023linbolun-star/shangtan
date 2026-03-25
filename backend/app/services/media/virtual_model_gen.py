"""
通义万相 虚拟模特生成服务

使用百炼API生成AI模特穿戴商品的效果图。
API文档：https://help.aliyun.com/zh/model-studio/virtual-model-generation
"""

import asyncio
import logging
import os
import time
import uuid

import httpx

from app.core.config import QWEN_API_KEY, ASSETS_DIR

logger = logging.getLogger("shangtanai.media.virtual_model")

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"


async def generate_virtual_model(
    gender: str = "female",
    age_range: str = "20-25",
    style_tags: list[str] | None = None,
    product_image_path: str | None = None,
) -> dict | None:
    """
    Generate a virtual AI model image.

    For MVP: Uses text-to-image with specific model-focused prompts.
    Future: Will use 通义万相's dedicated virtual model API when available.

    Args:
        gender: "female" or "male"
        age_range: e.g. "20-25"
        style_tags: style descriptors, e.g. ["韩系", "甜美"]
        product_image_path: optional path to product image for reference

    Returns:
        {"url": "...", "local_path": "...", "cost": 0.04} or None
    """
    if style_tags is None:
        style_tags = []

    api_key = QWEN_API_KEY
    if not api_key:
        logger.warning("QWEN_API_KEY not set, returning mock model")
        return {"url": "mock://model.jpg", "local_path": "", "cost": 0.0}

    # Build model description prompt
    gender_cn = "女性" if gender == "female" else "男性"
    age_desc = f"{age_range}岁"
    style_desc = "、".join(style_tags) if style_tags else "时尚简约"

    prompt = (
        f"电商模特照片，{gender_cn}，{age_desc}，{style_desc}风格，"
        f"正面半身照，干净白色背景，自然光线，高清商业摄影，不露脸或侧面"
    )
    negative_prompt = "变形、模糊、低质量、卡通、动漫"

    # Reuse existing image_gen
    from app.services.media.image_gen import generate_image

    results = await generate_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        size="768*1024",
        n=1,
    )

    if not results:
        return None

    return {
        "url": results[0].get("url", ""),
        "local_path": results[0].get("local_path", ""),
        "cost": results[0].get("cost", 0.04),
    }


async def generate_with_saved_model(
    product_image_path: str,
    model_reference_desc: str,
) -> dict | None:
    """
    Generate using a saved model reference description.

    Args:
        product_image_path: path to the product image
        model_reference_desc: text description of the saved model appearance

    Returns:
        {"url": "...", "local_path": "...", "cost": 0.04} or None
    """
    prompt = (
        f"电商模特穿戴商品效果图，{model_reference_desc}，"
        f"手持或穿戴商品展示，干净背景，高清商业摄影"
    )
    negative_prompt = "变形、模糊、低质量"

    from app.services.media.image_gen import generate_image

    results = await generate_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        size="768*1024",
        n=1,
    )

    if not results:
        return None

    return {
        "url": results[0].get("url", ""),
        "local_path": results[0].get("local_path", ""),
        "cost": 0.04,
    }
