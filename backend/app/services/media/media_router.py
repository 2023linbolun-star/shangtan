"""
媒体生成路由 -- 根据任务类型路由到最优模型。

类似 ai_engine.py 的模式，但用于图片/视频生成。
路由决策基于成本、质量和任务适配度。
"""

import logging

logger = logging.getLogger("shangtanai.media.router")

# 媒体生成模型路由表
# key: 任务类型, value: 首选模型
MEDIA_MODEL_MAP = {
    "main_image_white": "wanx",       # 白底图 -> 万相（最便宜 0.04 CNY）
    "main_image_scene": "jimeng",      # 场景图 -> 即梦（创意强 0.20 CNY）
    "main_image_detail": "wanx",       # 细节图 -> 万相
    "main_image_selling": "jimeng",    # 卖点图 -> 即梦
    "virtual_model": "wanx_model",     # 虚拟模特 -> 万相模特API
    "promo_video": "seedance",         # 宣传视频 -> 即梦 Seedance
    "promo_video_alt": "kling",        # 视频备选 -> 可灵
}

# 降级链：首选模型不可用时的 fallback
FALLBACK_CHAIN = {
    "jimeng": "wanx",
    "seedance": "ffmpeg",
    "kling": "ffmpeg",
    "wanx_model": "wanx",
}

# 模型成本参考（CNY per unit）
MODEL_COST_MAP = {
    "wanx": 0.04,       # per image
    "jimeng": 0.20,      # per image
    "wanx_model": 0.04,  # per image
    "seedance": 0.50,    # per second (avg)
    "kling": 0.30,       # per second (avg)
    "ffmpeg": 0.00,      # free (local processing)
}


def get_media_model(task_type: str) -> str:
    """
    获取任务对应的首选媒体模型。

    Args:
        task_type: one of the MEDIA_MODEL_MAP keys

    Returns:
        model identifier string, defaults to "wanx"
    """
    model = MEDIA_MODEL_MAP.get(task_type, "wanx")
    logger.debug(f"Routing task '{task_type}' to model '{model}'")
    return model


def get_fallback(model: str) -> str | None:
    """
    获取降级模型。

    Args:
        model: current model identifier

    Returns:
        fallback model identifier, or None if no fallback available
    """
    fallback = FALLBACK_CHAIN.get(model)
    if fallback:
        logger.info(f"Fallback for '{model}' -> '{fallback}'")
    return fallback


def estimate_cost(task_type: str, quantity: int = 1) -> float:
    """
    估算任务成本（CNY）。

    Args:
        task_type: task type key
        quantity: number of images or seconds of video

    Returns:
        estimated cost in CNY
    """
    model = get_media_model(task_type)
    unit_cost = MODEL_COST_MAP.get(model, 0.04)
    return round(unit_cost * quantity, 2)
