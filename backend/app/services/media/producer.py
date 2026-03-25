"""
内容生产编排器 — 将 AI 生成的脚本/文案转化为可发布的视频/图文。

输入：ContentAgent 的输出（脚本+策略+图片prompts+静态参数）
输出：可发布的视频文件 / 小红书图文包

编排流程：
  抖音：解析脚本 → 批量生图 → 场景配音 → 生成字幕 → FFmpeg合成视频
  小红书：解析文案 → 批量生图 → Pillow排版合成 → 输出图文包
"""

import json
import logging
import os
import uuid
from datetime import datetime

from app.core.config import ASSETS_DIR
from app.services.media import image_gen, tts, video_comp, xhs_compose
from app.services.media.tts import get_voice_for_category

logger = logging.getLogger("shangtanai.media.producer")


async def produce_douyin_video(
    content_output: dict,
    category: str = "default",
    bgm_path: str | None = None,
) -> dict:
    """
    抖音视频完整生产流程。

    Args:
        content_output: DouyinContentAgent 的输出
            - content: 脚本JSON字符串
            - strategy: 策略JSON字符串
            - image_prompts: 图片prompt JSON字符串
            - video_specs: 视频参数dict
        category: 产品品类（用于选择音色和BGM）
        bgm_path: 背景音乐路径，None则不加BGM

    Returns:
        {
            "video_path": "storage/assets/videos/xxx/final.mp4",
            "duration": 45.0,
            "file_size_mb": 12.3,
            "scenes": [...],
            "cost_breakdown": {"image": 0.2, "tts": 0.06, "total": 0.26},
        }
    """
    job_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(ASSETS_DIR, "videos", job_id)
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"[{job_id}] Starting Douyin video production")
    cost = {"image": 0.0, "tts": 0.0, "total": 0.0}

    # ── Step 1: 解析脚本和图片prompts ──
    script = _parse_json_safe(content_output.get("content", "{}"))
    image_prompts_data = _parse_json_safe(content_output.get("image_prompts", "{}"))

    scenes = script.get("scenes", [])
    if not scenes:
        logger.error(f"[{job_id}] No scenes in script")
        return {"video_path": "", "error": "脚本中没有场景数据"}

    scene_image_prompts = image_prompts_data.get("scene_images", [])

    logger.info(f"[{job_id}] Script has {len(scenes)} scenes")

    # ── Step 2: 批量生图（并发）──
    image_requests = []
    for i, scene in enumerate(scenes):
        # 优先使用生图专家的prompt，fallback到场景描述
        prompt_text = ""
        if i < len(scene_image_prompts):
            prompt_text = scene_image_prompts[i].get("prompt", "")
        if not prompt_text:
            prompt_text = scene.get("visual", f"电商产品展示图，{scene.get('shot_type', '中景')}")

        negative = ""
        if i < len(scene_image_prompts):
            negative = scene_image_prompts[i].get("negative_prompt", "")

        image_requests.append({
            "prompt": prompt_text,
            "negative_prompt": negative or "真人正脸，变形，模糊，低质量，水印",
        })

    # 封面图
    cover_prompt = image_prompts_data.get("cover_image", {})
    if cover_prompt.get("prompt"):
        image_requests.append({
            "prompt": cover_prompt["prompt"],
            "negative_prompt": cover_prompt.get("negative_prompt", ""),
        })

    logger.info(f"[{job_id}] Generating {len(image_requests)} images...")
    image_results = await image_gen.generate_batch(
        prompts=image_requests,
        size="1080*1920",  # 9:16
        save_dir=os.path.join(output_dir, "images"),
    )

    # 收集图片路径
    scene_images = []
    for r in image_results[:len(scenes)]:
        images = r.get("images", [])
        path = images[0]["local_path"] if images else ""
        scene_images.append(path)
        cost["image"] += r.get("cost", 0)

    # 封面图路径
    cover_path = ""
    if len(image_results) > len(scenes):
        cover_images = image_results[-1].get("images", [])
        cover_path = cover_images[0]["local_path"] if cover_images else ""

    logger.info(f"[{job_id}] Images generated, cost ¥{cost['image']:.2f}")

    # ── Step 3: 场景配音 ──
    voice = get_voice_for_category(category)
    tts_scenes = []
    for scene in scenes:
        tts_scenes.append({
            "scene_number": scene.get("scene_number", 0),
            "voiceover": scene.get("voiceover", ""),
        })

    logger.info(f"[{job_id}] Generating TTS for {len(tts_scenes)} scenes...")
    tts_results = await tts.synthesize_scenes(
        scenes=tts_scenes,
        voice=voice,
        save_dir=os.path.join(output_dir, "audio"),
    )

    scene_audios = []
    scene_durations = []
    for tr in tts_results:
        scene_audios.append(tr.get("local_path", ""))
        # 时长：优先TTS实际时长，fallback到脚本标注
        duration_ms = tr.get("duration_ms", 0)
        if duration_ms > 0:
            scene_durations.append(duration_ms / 1000.0)
        else:
            # 从场景标注提取时长
            scene_idx = tr.get("scene_number", 0) - 1
            if 0 <= scene_idx < len(scenes):
                duration_str = scenes[scene_idx].get("duration", "3秒")
                scene_durations.append(_parse_duration(duration_str))
            else:
                scene_durations.append(5.0)
        cost["tts"] += tr.get("cost", 0)

    logger.info(f"[{job_id}] TTS generated, cost ¥{cost['tts']:.4f}")

    # ── Step 4: 生成字幕 ──
    srt_scenes = []
    for i, scene in enumerate(scenes):
        srt_scenes.append({
            "scene_number": scene.get("scene_number", i + 1),
            "voiceover": scene.get("voiceover", ""),
            "duration_ms": int(scene_durations[i] * 1000) if i < len(scene_durations) else 3000,
        })

    srt_path = os.path.join(output_dir, "subtitles.srt")
    await video_comp.generate_srt(srt_scenes, srt_path)
    logger.info(f"[{job_id}] SRT generated")

    # ── Step 5: FFmpeg 合成视频 ──
    logger.info(f"[{job_id}] Composing video...")
    video_result = await video_comp.compose_video(
        scene_images=scene_images,
        scene_audios=scene_audios,
        scene_durations=scene_durations,
        srt_path=srt_path,
        bgm_path=bgm_path,
        output_dir=output_dir,
        platform="douyin",
    )

    cost["total"] = cost["image"] + cost["tts"]

    result = {
        "video_path": video_result.get("video_path", ""),
        "cover_path": cover_path,
        "duration": video_result.get("duration", 0),
        "file_size_mb": video_result.get("file_size_mb", 0),
        "title": script.get("title", ""),
        "hashtags": script.get("hashtags", []),
        "publishing_tips": script.get("publishing_tips", {}),
        "scenes_count": len(scenes),
        "cost_breakdown": cost,
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"[{job_id}] Douyin video complete: "
        f"{result['duration']}s, {result['file_size_mb']}MB, "
        f"cost ¥{cost['total']:.2f}"
    )
    return result


async def produce_xhs_images(
    content_output: dict,
    category: str = "default",
) -> dict:
    """
    小红书图文完整生产流程。

    Args:
        content_output: XHSContentAgent 的输出
            - content: 笔记JSON字符串
            - strategy: 策略JSON字符串
            - image_prompts: 图片prompt JSON字符串
            - image_specs: 图片参数dict

    Returns:
        {
            "images": ["path1.jpg", "path2.jpg", ...],
            "note_title": "标题",
            "note_content": "正文",
            "tags": [...],
            "cost_breakdown": {"image": 0.24, "total": 0.24},
        }
    """
    job_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(ASSETS_DIR, "xhs", job_id)
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"[{job_id}] Starting XHS image production")
    cost = {"image": 0.0, "total": 0.0}

    # ── Step 1: 解析文案和图片prompts ──
    note = _parse_json_safe(content_output.get("content", "{}"))
    image_prompts_data = _parse_json_safe(content_output.get("image_prompts", "{}"))

    title = note.get("title", "")
    content_text = note.get("content", "")
    tags = note.get("tags", [])
    image_suggestions = note.get("image_suggestions", [])

    image_prompt_list = image_prompts_data.get("images", [])
    if not image_prompt_list:
        logger.warning(f"[{job_id}] No image prompts, using fallback")
        # Fallback: 用笔记中的image_suggestions
        image_prompt_list = [
            {"prompt": suggestion, "negative_prompt": "", "text_overlay": "", "position": f"图{i+1}"}
            for i, suggestion in enumerate(image_suggestions[:6])
        ]

    logger.info(f"[{job_id}] Note: '{title}', generating {len(image_prompt_list)} images")

    # ── Step 2: 批量生图（并发）──
    gen_requests = []
    for ip in image_prompt_list[:6]:
        gen_requests.append({
            "prompt": ip.get("prompt", "电商产品展示图"),
            "negative_prompt": ip.get("negative_prompt", "真人正脸，变形，模糊，低质量，水印"),
        })

    image_results = await image_gen.generate_batch(
        prompts=gen_requests,
        size="1080*1440",  # 3:4 小红书竖版
        save_dir=os.path.join(output_dir, "raw_images"),
    )

    raw_image_paths = []
    for r in image_results:
        images = r.get("images", [])
        path = images[0]["local_path"] if images else ""
        raw_image_paths.append(path)
        cost["image"] += r.get("cost", 0)

    logger.info(f"[{job_id}] Raw images generated, cost ¥{cost['image']:.2f}")

    # ── Step 3: Pillow 排版合成 ──
    # 构建每张图的文字信息
    image_texts = []
    for i, ip in enumerate(image_prompt_list[:6]):
        text_overlay = ip.get("text_overlay", "")
        # 从策略中提取headline和body
        headline = ""
        body = ""
        if i == 0:
            headline = title
            body = content_text[:50] if content_text else ""
        else:
            # 用image_prompt中的position作为headline
            headline = ip.get("position", f"图{i+1}")
            body = text_overlay or ""

        image_texts.append({
            "headline": headline,
            "body": body,
            "text_overlay": text_overlay,
        })

    composed_images = xhs_compose.compose_full_set(
        image_paths=raw_image_paths,
        image_texts=image_texts,
        title=title,
        output_dir=os.path.join(output_dir, "final"),
    )

    cost["total"] = cost["image"]

    result = {
        "images": composed_images,
        "raw_images": raw_image_paths,
        "note_title": title,
        "note_content": content_text,
        "tags": tags,
        "publishing_tips": note.get("publishing_tips", {}),
        "image_count": len(composed_images),
        "cost_breakdown": cost,
        "job_id": job_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"[{job_id}] XHS images complete: "
        f"{len(composed_images)} images, "
        f"cost ¥{cost['total']:.2f}"
    )
    return result


async def produce_content(
    content_output: dict,
    platform: str,
    category: str = "default",
    bgm_path: str | None = None,
) -> dict:
    """
    统一入口：根据平台自动选择生产流程。

    Args:
        content_output: ContentAgent 子agent的输出
        platform: 目标平台
        category: 产品品类
        bgm_path: BGM路径（仅抖音）

    Returns:
        平台对应的生产结果
    """
    if platform in ("douyin", "kuaishou"):
        return await produce_douyin_video(content_output, category, bgm_path)
    elif platform == "xiaohongshu":
        return await produce_xhs_images(content_output, category)
    else:
        # 淘宝/拼多多不需要素材生产，直接返回文案
        return {
            "platform": platform,
            "content": content_output.get("content", ""),
            "cost_breakdown": {"total": 0},
        }


async def produce_all(
    content_outputs: list[dict],
    category: str = "default",
    bgm_path: str | None = None,
) -> list[dict]:
    """
    批量生产所有平台的内容素材。

    Args:
        content_outputs: ContentAgent 的 generated_contents 列表
        category: 产品品类
        bgm_path: BGM路径

    Returns:
        各平台的生产结果列表
    """
    results = []
    for output in content_outputs:
        platform = output.get("platform", "")
        try:
            result = await produce_content(output, platform, category, bgm_path)
            result["platform"] = platform
            result["status"] = "success"
            results.append(result)
        except Exception as e:
            logger.error(f"Production failed for {platform}: {e}")
            results.append({
                "platform": platform,
                "status": "failed",
                "error": str(e),
            })

    return results


# ── 工具函数 ──

def _parse_json_safe(text: str) -> dict:
    """安全解析JSON，处理markdown代码块和异常情况。"""
    if not text:
        return {}

    # 去除markdown代码块标记
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # 去掉首尾的```行
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 尝试找到第一个{到最后一个}
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass
        logger.warning(f"Failed to parse JSON: {cleaned[:100]}...")
        return {}


def _parse_duration(duration_str: str) -> float:
    """解析场景时长字符串，如 '0-3秒' → 3.0, '10-30秒' → 20.0。"""
    import re
    numbers = re.findall(r'[\d.]+', duration_str)
    if len(numbers) >= 2:
        return float(numbers[1]) - float(numbers[0])
    elif numbers:
        return float(numbers[0])
    return 5.0  # 默认5秒
