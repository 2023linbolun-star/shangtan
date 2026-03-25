"""
即梦 Jimeng AI 生图服务（火山引擎）

与豆包/火山TTS共用火山引擎平台。
模型：即梦 Jimeng 4.5
定价：约 0.20 CNY/张

MVP阶段：如果 JIMENG_API_KEY 未设置，降级到通义万相。
"""

import asyncio
import logging
import os
import uuid

import httpx

from app.core.config import JIMENG_API_KEY, ASSETS_DIR

logger = logging.getLogger("shangtanai.media.jimeng")

JIMENG_BASE = "https://visual.volcengineapi.com"


async def generate_image_jimeng(
    prompt: str,
    negative_prompt: str = "",
    size: str = "1024*1024",
    n: int = 1,
    save_dir: str | None = None,
) -> list[dict]:
    """
    调用即梦生成图片。

    MVP阶段：如果 JIMENG_API_KEY 未设置，降级到通义万相。

    Args:
        prompt: 中文生图描述
        negative_prompt: 不要出现的元素
        size: 图片尺寸，如 "1024*1024"
        n: 生成数量（1-4）
        save_dir: 保存目录，None 则自动创建

    Returns:
        [{"url": "...", "local_path": "...", "cost": ...}, ...]
    """
    if not JIMENG_API_KEY:
        logger.info("JIMENG_API_KEY not set, falling back to Wanx")
        from app.services.media.image_gen import generate_image

        return await generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            size=size,
            n=n,
            save_dir=save_dir,
        )

    # TODO: Implement actual Jimeng API call when API key is available
    # Reference: https://www.volcengine.com/docs/6791/jimeng-api
    #
    # The integration will follow this pattern:
    # 1. POST to JIMENG_BASE/v1/images/generations with model, prompt, size
    # 2. Poll task status until SUCCEEDED or FAILED
    # 3. Download result images to save_dir
    # 4. Return list of {"url", "local_path", "cost"} dicts
    #
    # For now, fallback to Wanx
    logger.info("Jimeng API integration pending, using Wanx fallback")
    from app.services.media.image_gen import generate_image

    return await generate_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        size=size,
        n=n,
        save_dir=save_dir,
    )
