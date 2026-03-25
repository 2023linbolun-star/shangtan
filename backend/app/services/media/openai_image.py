"""
OpenAI GPT Image 1.5 图片生成/编辑服务

支持：
- 文生图：text → image
- 图生图：image + text → image（编辑模式，保留原图元素）

base64 直传，不需要公网 URL。
"""

import base64
import logging
import os
import uuid

import httpx

from app.core.config import OPENAI_API_KEY, ASSETS_DIR

logger = logging.getLogger("shangtanai.media.openai_image")

OPENAI_IMAGE_URL = "https://api.openai.com/v1/images"


async def generate_image_openai(
    prompt: str,
    ref_image_path: str | None = None,
    size: str = "1024x1024",
    quality: str = "medium",
    save_dir: str | None = None,
) -> dict:
    """
    调用 OpenAI GPT Image 1.5 生成图片。

    Args:
        prompt: 图片描述（中英文均可）
        ref_image_path: 参考图片路径（有则为图生图/编辑模式）
        size: 输出尺寸 "1024x1024" / "1536x1024" / "1024x1536"
        quality: "low" / "medium" / "high"
        save_dir: 保存目录

    Returns:
        {"url": "/static/assets/...", "local_path": "...", "cost": ...}
    """
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set")
        return {"url": "", "local_path": "", "cost": 0.0}

    save_dir = save_dir or os.path.join(ASSETS_DIR, "openai_images", uuid.uuid4().hex[:8])
    os.makedirs(save_dir, exist_ok=True)

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    try:
        if ref_image_path and os.path.isfile(ref_image_path):
            # 图生图（编辑模式）：上传参考图 + prompt
            result = await _edit_image(prompt, ref_image_path, size, quality, headers, save_dir)
        else:
            # 纯文生图
            result = await _generate_image(prompt, size, quality, headers, save_dir)

        return result

    except Exception as e:
        logger.exception(f"OpenAI image generation failed: {e}")
        return {"url": "", "local_path": "", "cost": 0.0}


async def _generate_image(
    prompt: str, size: str, quality: str, headers: dict, save_dir: str,
) -> dict:
    """纯文生图：POST /v1/images/generations"""
    body = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "output_format": "b64_json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OPENAI_IMAGE_URL}/generations",
            headers={**headers, "Content-Type": "application/json"},
            json=body,
            timeout=120,
        )

    if resp.status_code != 200:
        error = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
        logger.error(f"OpenAI image gen failed: {resp.status_code} {error}")
        return {"url": "", "local_path": "", "cost": 0.0}

    data = resp.json()
    return _save_result(data, save_dir, quality)


async def _edit_image(
    prompt: str, image_path: str, size: str, quality: str, headers: dict, save_dir: str,
) -> dict:
    """图生图（编辑模式）：POST /v1/images/edits，multipart 上传"""

    # 读取图片文件
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # 确定文件名和 mime type
    ext = os.path.splitext(image_path)[1].lower()
    filename = f"ref{ext}"

    # multipart form data
    files = {
        "image": (filename, image_bytes, "image/png" if ext == ".png" else "image/jpeg"),
    }
    form_data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "n": "1",
        "size": size,
        "quality": quality,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OPENAI_IMAGE_URL}/edits",
            headers=headers,  # 不设 Content-Type，让 httpx 自动设 multipart
            data=form_data,
            files=files,
            timeout=120,
        )

    if resp.status_code != 200:
        error = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
        logger.error(f"OpenAI image edit failed: {resp.status_code} {error}")
        # 降级到纯文生图
        logger.info("Falling back to text-to-image generation")
        return await _generate_image(prompt, size, quality, headers, save_dir)

    data = resp.json()
    return _save_result(data, save_dir, quality)


def _save_result(data: dict, save_dir: str, quality: str) -> dict:
    """保存 OpenAI 返回的图片结果。"""
    images = data.get("data", [])
    if not images:
        logger.error(f"OpenAI returned no images: {data}")
        return {"url": "", "local_path": "", "cost": 0.0}

    img_data = images[0]
    out_path = os.path.join(save_dir, "result.png")

    # 优先用 b64_json
    if img_data.get("b64_json"):
        img_bytes = base64.b64decode(img_data["b64_json"])
        with open(out_path, "wb") as f:
            f.write(img_bytes)
    elif img_data.get("url"):
        # 如果返回的是 URL，下载
        import httpx as _httpx
        resp = _httpx.get(img_data["url"], timeout=30)
        with open(out_path, "wb") as f:
            f.write(resp.content)
    else:
        return {"url": "", "local_path": "", "cost": 0.0}

    # 生成静态 URL
    relative = out_path.split(ASSETS_DIR)[-1].lstrip("/\\")
    url = f"/static/assets/{relative}"

    # 估算成本
    cost_map = {"low": 0.02, "medium": 0.07, "high": 0.19}
    cost = cost_map.get(quality, 0.07)

    logger.info(f"OpenAI image saved: {out_path} (quality={quality}, cost=${cost})")
    return {"url": url, "local_path": out_path, "cost": cost}
