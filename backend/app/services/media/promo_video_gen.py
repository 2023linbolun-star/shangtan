"""
商品宣传视频生成编排器

编排脚本生成 -> 场景图 -> 配音 -> 视频合成的完整流程。
"""

import asyncio
import logging
import os
import uuid

from app.services.ai_engine import ai_analyze_full
from app.services.media.seedance_gen import generate_video_seedance
from app.core.config import ASSETS_DIR

logger = logging.getLogger("shangtanai.media.promo_video")


async def generate_promo_video(
    product_info: str,
    product_images: list[str] | None = None,
    model_asset_id: str | None = None,
    duration: int = 15,
    voice: str | None = None,
) -> dict | None:
    """
    生成商品宣传视频。

    流程：
    1. AI 生成宣传脚本（旁白文案）
    2. 收集场景图（商品图 + 可选模特图）
    3. 调用 Seedance 生成视频（或 FFmpeg 降级）

    Args:
        product_info: product name and description
        product_images: list of local image paths
        model_asset_id: optional saved virtual model asset ID
        duration: target video duration in seconds (default 15)
        voice: optional TTS voice ID override

    Returns:
        {"video_path": "...", "video_url": "...", "duration": N,
         "cost": ..., "script": "..."} or None
    """
    save_dir = os.path.join(ASSETS_DIR, "videos", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    # Step 1: Generate voiceover script via AI
    script_prompt = (
        f"为以下商品生成一段{duration}秒的电商展示视频脚本。\n"
        f"要求：简洁有力，突出卖点，适合商品详情页顶部展示。\n"
        f"只需要旁白文案，不需要场景描述。控制在{duration * 2}字以内。\n\n"
        f"商品信息：{product_info}"
    )

    try:
        script_result = await ai_analyze_full(
            script_prompt, task_type="content_social"
        )
        script_text = script_result.get("text", product_info[:50])
    except Exception as e:
        logger.warning(f"Script generation failed, using product info excerpt: {e}")
        script_text = product_info[:80]

    # Step 2: Collect images
    images = product_images or []

    # Step 2.5: Generate creative motion description via SceneArchitect
    video_prompt = script_text
    if images:
        try:
            motion_prompt = (
                f"你是一位电商视频创意导演。根据以下商品信息，生成一段适合AI视频生成的运镜描述。\n\n"
                f"商品信息：{product_info}\n"
                f"旁白文案：{script_text}\n\n"
                f"要求：\n"
                f"- 描述镜头运动（推拉摇移、特写过渡等）\n"
                f"- 描述光影变化和氛围感\n"
                f"- 适合Seedance视频生成模型的英文+中文混合prompt\n"
                f"- 控制在100字以内\n\n"
                f"只输出运镜描述，不要其他内容。"
            )
            motion_result = await ai_analyze_full(
                motion_prompt, task_type="scene_architect"
            )
            motion_text = motion_result.get("text", "").strip()
            if motion_text:
                video_prompt = motion_text
                logger.info(f"SceneArchitect generated motion description: {motion_text[:80]}")
        except Exception as e:
            logger.warning(f"SceneArchitect motion generation failed, using script: {e}")

    # Step 3: Generate video
    result = await generate_video_seedance(
        images=images,
        script=video_prompt,
        duration=duration,
        save_dir=save_dir,
    )

    if result:
        result["script"] = script_text

    return result
