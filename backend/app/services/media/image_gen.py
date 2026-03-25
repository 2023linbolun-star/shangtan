"""
通义万相 AI 生图服务

使用 DashScope API（和通义千问共用同一个API Key）。
模型：wanx2.1-t2i-turbo（快速版，~5秒/张，0.04元/张）

API文档：https://help.aliyun.com/zh/model-studio/text-to-image
"""

import asyncio
import logging
import os
import time
import uuid

import httpx

from app.core.config import QWEN_API_KEY, WANX_MODEL, ASSETS_DIR

logger = logging.getLogger("shangtanai.media.image_gen")

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"


async def generate_image(
    prompt: str,
    negative_prompt: str = "",
    size: str = "1080*1920",
    n: int = 1,
    save_dir: str | None = None,
) -> list[dict]:
    """
    调用通义万相生成图片。

    Args:
        prompt: 中文生图描述
        negative_prompt: 不要出现的元素
        size: 图片尺寸，如 "1080*1920"(9:16) 或 "1080*1440"(3:4)
        n: 生成数量（1-4）
        save_dir: 保存目录，None则自动创建

    Returns:
        [{"url": "...", "local_path": "...", "cost": 0.04}, ...]
    """
    api_key = QWEN_API_KEY  # DashScope统一Key
    if not api_key:
        logger.warning("QWEN_API_KEY not set, returning mock image")
        return [{"url": f"mock://image_{i}.jpg", "local_path": "", "cost": 0.0} for i in range(n)]

    # Step 1: 提交生图任务
    task_url = f"{DASHSCOPE_BASE}/services/aigc/text2image/image-synthesis"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",  # 异步模式
    }
    body = {
        "model": WANX_MODEL,
        "input": {
            "prompt": prompt,
        },
        "parameters": {
            "size": size,
            "n": n,
        },
    }
    if negative_prompt:
        body["input"]["negative_prompt"] = negative_prompt

    start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        resp = await client.post(task_url, headers=headers, json=body, timeout=30)
        data = resp.json()

    task_id = data.get("output", {}).get("task_id")
    if not task_id:
        error = data.get("message", str(data))
        logger.error(f"Image gen submit failed: {error}")
        return []

    # Step 2: 轮询任务结果
    status_url = f"{DASHSCOPE_BASE}/tasks/{task_id}"
    status_headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(60):  # 最多等60秒
        await asyncio.sleep(1)
        async with httpx.AsyncClient() as client:
            resp = await client.get(status_url, headers=status_headers, timeout=10)
            status_data = resp.json()

        task_status = status_data.get("output", {}).get("task_status")
        if task_status == "SUCCEEDED":
            break
        elif task_status == "FAILED":
            error = status_data.get("output", {}).get("message", "unknown")
            logger.error(f"Image gen failed: {error}")
            return []
    else:
        logger.error(f"Image gen timeout after 60s, task_id={task_id}")
        return []

    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    # Step 3: 提取结果并下载
    results_list = status_data.get("output", {}).get("results", [])
    if not results_list:
        return []

    save_dir = save_dir or os.path.join(ASSETS_DIR, "images", str(uuid.uuid4())[:8])
    os.makedirs(save_dir, exist_ok=True)

    images = []
    for i, result in enumerate(results_list):
        url = result.get("url", "")
        if not url:
            continue

        # 下载到本地
        filename = f"img_{i:02d}.jpg"
        local_path = os.path.join(save_dir, filename)

        try:
            async with httpx.AsyncClient() as client:
                img_resp = await client.get(url, timeout=30)
                with open(local_path, "wb") as f:
                    f.write(img_resp.content)
        except Exception as e:
            logger.warning(f"Failed to download image {i}: {e}")
            local_path = ""

        images.append({
            "url": url,
            "local_path": local_path,
            "cost": 0.04,  # 通义万相turbo定价
        })

    logger.info(f"Generated {len(images)} images in {duration_ms}ms, task_id={task_id}")
    return images


async def generate_batch(
    prompts: list[dict],
    size: str = "1080*1920",
    save_dir: str | None = None,
) -> list[dict]:
    """
    批量生成图片（并发执行）。

    Args:
        prompts: [{"prompt": "...", "negative_prompt": "..."}, ...]
        size: 统一尺寸
        save_dir: 保存根目录

    Returns:
        [{"scene": 0, "images": [...], "cost": 0.04}, ...]
    """
    save_dir = save_dir or os.path.join(ASSETS_DIR, "images", str(uuid.uuid4())[:8])

    tasks = []
    for i, p in enumerate(prompts):
        scene_dir = os.path.join(save_dir, f"scene_{i:02d}")
        tasks.append(
            generate_image(
                prompt=p["prompt"],
                negative_prompt=p.get("negative_prompt", ""),
                size=size,
                n=1,
                save_dir=scene_dir,
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    batch_results = []
    total_cost = 0
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.warning(f"Scene {i} generation failed: {r}")
            batch_results.append({"scene": i, "images": [], "cost": 0})
        else:
            cost = sum(img.get("cost", 0) for img in r)
            total_cost += cost
            batch_results.append({"scene": i, "images": r, "cost": cost})

    logger.info(f"Batch complete: {len(prompts)} scenes, total cost ¥{total_cost:.2f}")
    return batch_results
