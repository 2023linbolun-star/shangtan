"""
即梦 Seedance 1.5 Pro 视频生成服务（火山引擎 ARK API）

图生视频：提交图片 + 文本 prompt → 异步生成视频。
API: POST {DOUBAO_BASE_URL}/contents/generations/tasks

降级方案：DOUBAO_API_KEY 未配置时用 FFmpeg 幻灯片。
"""

import asyncio
import base64
import logging
import os
import uuid

import httpx

from app.core.config import (
    DOUBAO_API_KEY,
    DOUBAO_BASE_URL,
    SEEDANCE_MODEL,
    ASSETS_DIR,
)

logger = logging.getLogger("shangtanai.media.seedance")

# 任务轮询配置
POLL_INTERVAL = 5  # 秒
POLL_MAX_WAIT = 300  # 最多等 5 分钟


async def generate_video_seedance(
    images: list[str],
    script: str = "",
    duration: int = 5,
    save_dir: str | None = None,
) -> dict | None:
    """
    调用即梦 Seedance 1.5 Pro 图生视频。

    Args:
        images: 本地图片文件路径列表（取第一张作为输入）
        script: 视频运镜/内容描述 prompt
        duration: 视频时长（秒），Seedance 支持 5/10
        save_dir: 输出目录

    Returns:
        {"video_path": "...", "video_url": "...", "duration": N, "cost": ...} or None
    """
    if not DOUBAO_API_KEY:
        logger.info("DOUBAO_API_KEY not set, using FFmpeg fallback")
        return await _ffmpeg_fallback(images, script, duration, save_dir)

    # 找到第一张有效图片
    valid_images = [img for img in images if os.path.exists(img)]
    if not valid_images:
        logger.error("No valid images for Seedance video generation")
        return None

    image_path = valid_images[0]
    save_dir = save_dir or os.path.join(ASSETS_DIR, "videos", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    try:
        # Step 1: 将本地图片转为 data URI
        image_data_uri = _image_to_data_uri(image_path)

        # Step 2: 构建请求
        # Seedance duration 参数通过 prompt 末尾 --duration 指定
        seedance_duration = min(duration, 10)  # Seedance 最长 10 秒
        prompt_text = script or "商品展示，缓慢旋转，专业产品广告"
        prompt_text += f"  --duration {seedance_duration}"

        task_url = f"{DOUBAO_BASE_URL}/contents/generations/tasks"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DOUBAO_API_KEY}",
        }
        body = {
            "model": SEEDANCE_MODEL,
            "content": [
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": image_data_uri}},
            ],
        }

        logger.info("Submitting Seedance task: model=%s, duration=%ds", SEEDANCE_MODEL, seedance_duration)

        async with httpx.AsyncClient() as client:
            resp = await client.post(task_url, headers=headers, json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()

        task_id = data.get("id")
        if not task_id:
            logger.error("Seedance task submit failed: %s", data)
            return await _ffmpeg_fallback(images, script, duration, save_dir)

        logger.info("Seedance task submitted: task_id=%s", task_id)

        # Step 3: 轮询任务状态
        status_url = f"{DOUBAO_BASE_URL}/contents/generations/tasks/{task_id}"
        video_url_remote = None

        for _ in range(POLL_MAX_WAIT // POLL_INTERVAL):
            await asyncio.sleep(POLL_INTERVAL)

            async with httpx.AsyncClient() as client:
                resp = await client.get(status_url, headers=headers, timeout=15)
                resp.raise_for_status()
                status_data = resp.json()

            status = status_data.get("status", "")
            if status == "succeeded":
                # 提取视频 URL
                content = status_data.get("content", {})
                # 尝试多种可能的返回结构
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "video_url":
                            video_url_remote = item.get("video_url", {}).get("url", "")
                            break
                elif isinstance(content, dict):
                    video_url_remote = content.get("video_url", {}).get("url", "")
                    if not video_url_remote:
                        video_url_remote = content.get("url", "")

                # 也检查顶层
                if not video_url_remote:
                    video_url_remote = status_data.get("video_url", "")
                if not video_url_remote:
                    outputs = status_data.get("output", {})
                    if isinstance(outputs, dict):
                        video_url_remote = outputs.get("video_url", "")

                break
            elif status == "failed":
                error = status_data.get("error", {})
                logger.error("Seedance task failed: %s", error)
                return await _ffmpeg_fallback(images, script, duration, save_dir)
        else:
            logger.error("Seedance task timeout after %ds, task_id=%s", POLL_MAX_WAIT, task_id)
            return await _ffmpeg_fallback(images, script, duration, save_dir)

        if not video_url_remote:
            logger.error("Seedance succeeded but no video URL found: %s", status_data)
            return await _ffmpeg_fallback(images, script, duration, save_dir)

        # Step 4: 下载视频到本地
        video_filename = f"seedance_{uuid.uuid4().hex[:8]}.mp4"
        video_path = os.path.join(save_dir, video_filename)

        async with httpx.AsyncClient() as client:
            video_resp = await client.get(video_url_remote, timeout=60)
            with open(video_path, "wb") as f:
                f.write(video_resp.content)

        dir_name = os.path.basename(save_dir)
        local_url = f"/static/assets/videos/{dir_name}/{video_filename}"

        logger.info("Seedance video downloaded: %s (%d bytes)", video_path, len(video_resp.content))

        return {
            "video_path": video_path,
            "video_url": local_url,
            "duration": seedance_duration,
            "cost": seedance_duration * 0.5,  # 约 0.5 元/秒
        }

    except Exception as e:
        logger.exception("Seedance API call failed: %s", e)
        return await _ffmpeg_fallback(images, script, duration, save_dir)


def _image_to_data_uri(image_path: str) -> str:
    """将本地图片转为 data URI（base64编码）。"""
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime = mime_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime};base64,{encoded}"


async def _ffmpeg_fallback(
    images: list[str],
    script: str,
    duration: int,
    save_dir: str | None,
) -> dict | None:
    """
    降级方案: 使用 FFmpeg 将图片合成为简单轮播视频 + TTS 配音。
    """
    try:
        from app.services.media.video_comp import compose_video
        from app.services.media.tts import synthesize

        save_dir = save_dir or os.path.join(
            ASSETS_DIR, "videos", uuid.uuid4().hex[:8]
        )
        os.makedirs(save_dir, exist_ok=True)

        # Generate voiceover if script provided
        audio_path = None
        if script:
            try:
                audio_result = await synthesize(script, output_dir=save_dir)
                audio_path = audio_result.get("audio_path")
            except Exception as e:
                logger.warning(f"TTS failed, continuing without audio: {e}")

        video_path = os.path.join(save_dir, "promo.mp4")

        valid_images = [img for img in images if os.path.exists(img)]
        if not valid_images:
            logger.error("No valid images for video generation")
            return None

        dur_per_image = max(3, duration // len(valid_images))

        await compose_video(
            image_paths=valid_images,
            audio_path=audio_path,
            output_path=video_path,
            duration_per_image=dur_per_image,
        )

        dir_name = os.path.basename(save_dir)
        return {
            "video_path": video_path,
            "video_url": f"/static/assets/videos/{dir_name}/promo.mp4",
            "duration": duration,
            "cost": 0.0,
        }
    except Exception as e:
        logger.error(f"FFmpeg video fallback failed: {e}")
        return None
