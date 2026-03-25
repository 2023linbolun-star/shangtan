"""
火山引擎 TTS 配音服务

使用火山引擎语音合成 API（大模型语音合成 - 双向流式）。
定价：约0.2元/千字。

支持音色：
- zh_female_shuangkuaisisi_moon_bigtts  双快丝丝（活力女声，适合种草带货）
- zh_male_chunhou_moon_bigtts           醇厚男声（适合科技评测）
- zh_female_wanwanxiaohe_moon_bigtts    弯弯小何（温柔女声，适合美妆）

API文档：https://www.volcengine.com/docs/6561/1257543
"""

import base64
import gzip
import json
import logging
import os
import struct
import time
import uuid

import httpx

from app.core.config import VOLCENGINE_ACCESS_KEY, VOLCENGINE_APP_ID, VOLCENGINE_TTS_VOICE, ASSETS_DIR

logger = logging.getLogger("shangtanai.media.tts")

TTS_API_URL = "https://openspeech.bytedance.com/api/v1/tts"


async def synthesize(
    text: str,
    voice: str | None = None,
    speed_ratio: float = 1.0,
    save_dir: str | None = None,
    filename: str | None = None,
) -> dict:
    """
    调用火山引擎TTS合成语音。

    Args:
        text: 要合成的文字
        voice: 音色ID，None使用默认配置
        speed_ratio: 语速（0.5-2.0，1.0为正常）
        save_dir: 保存目录
        filename: 文件名

    Returns:
        {"local_path": "...", "duration_ms": 3500, "cost": 0.06, "char_count": 300}
    """
    voice = voice or VOLCENGINE_TTS_VOICE

    if not VOLCENGINE_ACCESS_KEY or not VOLCENGINE_APP_ID:
        logger.warning("Volcengine TTS not configured, returning mock")
        return {
            "local_path": "",
            "duration_ms": len(text) * 200,  # 粗估
            "cost": 0.0,
            "char_count": len(text),
        }

    save_dir = save_dir or os.path.join(ASSETS_DIR, "audio")
    os.makedirs(save_dir, exist_ok=True)
    filename = filename or f"tts_{uuid.uuid4().hex[:8]}.mp3"
    local_path = os.path.join(save_dir, filename)

    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer;{VOLCENGINE_ACCESS_KEY}",
    }
    body = {
        "app": {
            "appid": VOLCENGINE_APP_ID,
            "token": "access_token",
            "cluster": "volcano_tts",
        },
        "user": {"uid": "shangtanai"},
        "audio": {
            "voice_type": voice,
            "encoding": "mp3",
            "speed_ratio": speed_ratio,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query",
        },
    }

    start = time.perf_counter()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(TTS_API_URL, headers=headers, json=body, timeout=60)
            data = resp.json()

        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # 解析返回的音频数据
        audio_data = data.get("data", "")
        if not audio_data:
            error = data.get("message", str(data))
            logger.error(f"TTS failed: {error}")
            return {"local_path": "", "duration_ms": 0, "cost": 0, "char_count": len(text)}

        # base64解码保存
        audio_bytes = base64.b64decode(audio_data)
        with open(local_path, "wb") as f:
            f.write(audio_bytes)

        # 估算音频时长（按中文平均语速5字/秒）
        estimated_duration = len(text) / 5.0 * 1000 / speed_ratio
        # 成本估算（0.2元/千字）
        cost = len(text) * 0.0002

        logger.info(f"TTS complete: {len(text)} chars, {duration_ms}ms api time, cost ¥{cost:.4f}")

        return {
            "local_path": local_path,
            "duration_ms": estimated_duration,
            "cost": cost,
            "char_count": len(text),
        }

    except Exception as e:
        logger.error(f"TTS request failed: {e}")
        return {"local_path": "", "duration_ms": 0, "cost": 0, "char_count": len(text)}


async def synthesize_scenes(
    scenes: list[dict],
    voice: str | None = None,
    speed_ratio: float = 1.0,
    save_dir: str | None = None,
) -> list[dict]:
    """
    为视频脚本的每个场景生成配音（串行执行，保证顺序）。

    Args:
        scenes: [{"scene_number": 1, "voiceover": "文案..."}, ...]
        voice: 音色ID
        speed_ratio: 语速

    Returns:
        [{"scene_number": 1, "local_path": "...", "duration_ms": 3000, "cost": 0.06}, ...]
    """
    save_dir = save_dir or os.path.join(ASSETS_DIR, "audio", str(uuid.uuid4())[:8])
    os.makedirs(save_dir, exist_ok=True)

    results = []
    total_cost = 0

    for scene in scenes:
        text = scene.get("voiceover", "")
        if not text:
            results.append({
                "scene_number": scene.get("scene_number", 0),
                "local_path": "",
                "duration_ms": 0,
                "cost": 0,
            })
            continue

        filename = f"scene_{scene.get('scene_number', 0):02d}.mp3"
        result = await synthesize(
            text=text,
            voice=voice,
            speed_ratio=speed_ratio,
            save_dir=save_dir,
            filename=filename,
        )

        total_cost += result.get("cost", 0)
        results.append({
            "scene_number": scene.get("scene_number", 0),
            "local_path": result["local_path"],
            "duration_ms": result["duration_ms"],
            "cost": result["cost"],
        })

    logger.info(f"Scenes TTS complete: {len(scenes)} scenes, total cost ¥{total_cost:.4f}")
    return results


# ── 音色推荐 ──

VOICE_PRESETS = {
    "fashion": "zh_female_shuangkuaisisi_moon_bigtts",     # 活力女声
    "beauty": "zh_female_wanwanxiaohe_moon_bigtts",         # 温柔女声
    "food": "zh_female_shuangkuaisisi_moon_bigtts",         # 活力女声
    "tech": "zh_male_chunhou_moon_bigtts",                  # 醇厚男声
    "sport": "zh_male_chunhou_moon_bigtts",                 # 醇厚男声
    "home": "zh_female_wanwanxiaohe_moon_bigtts",           # 温柔女声
    "mother_baby": "zh_female_wanwanxiaohe_moon_bigtts",    # 温柔女声
    "default": "zh_female_shuangkuaisisi_moon_bigtts",      # 默认活力女声
}


def get_voice_for_category(category: str) -> str:
    """根据品类推荐最合适的音色。"""
    return VOICE_PRESETS.get(category, VOICE_PRESETS["default"])
