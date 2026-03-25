"""
视频合成技术参数 — 静态规则（来源：短视频编辑专家）
FFmpeg合成、字幕、音频、导出全部参数在此定义。
"""

# ── 视频画面 ──

DOUYIN_VIDEO = {
    "resolution": "1080x1920",
    "width": 1080,
    "height": 1920,
    "aspect_ratio": "9:16",
    "fps": 30,
    "bitrate": "10M",
    "codec": "libx264",
    "preset": "medium",
    "pix_fmt": "yuv420p",
    "duration_range": (30, 60),  # 秒
}

KUAISHOU_VIDEO = {**DOUYIN_VIDEO}  # 规格相同

XHS_IMAGE = {
    "cover_size": (1080, 1440),  # 3:4 竖版封面
    "body_size": (1080, 1440),
    "format": "jpg",
    "quality": 95,
    "max_images": 9,  # 小红书最多9张图
    "recommended_images": 6,  # 建议6张
}

# ── 字幕规格 ──

SUBTITLE = {
    # 字体选择（免费商用）
    "fonts": [
        "Source Han Sans CN Medium",  # 思源黑体
        "Alibaba PuHuiTi 2.0 55 Regular",  # 阿里巴巴普惠体
    ],
    "fallback_font": "Noto Sans CJK SC",
    "font_size": 36,  # px，竖屏正文
    "title_font_size": 56,
    "color": "#FFFFFF",
    "stroke_color": "#000000",
    "stroke_width": 2,
    # 安全区域（距离边缘百分比）
    "margin_top_pct": 0.15,
    "margin_bottom_pct": 0.15,  # 底部15%是平台控件区
    "margin_side_pct": 0.05,
    # 时间控制
    "min_duration": 1.0,  # 秒
    "max_duration": 5.0,
    "lead_time": 0.2,  # 提前显示0.2秒
    # 背景
    "bg_opacity": 0.6,  # 半透明黑底
    "bg_padding": 8,
}

# ── 音频规格 ──

AUDIO = {
    # 配音
    "voice_db_range": (-12, -6),  # dBFS
    "voice_sample_rate": 24000,
    "voice_format": "mp3",
    # BGM
    "bgm_db": -22,  # dBFS，不能盖过人声
    "bgm_fade_in": 1.0,  # 秒
    "bgm_fade_out": 2.0,
    # 最终响度
    "target_loudness": -14,  # LUFS
    "codec": "aac",
    "bitrate": "192k",
}

# ── Ken Burns 动效参数（图片变视频）──

KEN_BURNS = {
    "zoom_range": (1.0, 1.15),  # 从1.0倍缓慢放大到1.15倍
    "pan_speed": 30,  # px/秒，平移速度
    "transition_duration": 0.5,  # 场景切换过渡时间（秒）
    "transition_type": "fade",  # fade / dissolve / slide
}

# ── BGM 风格库（按品类预置）──

BGM_STYLES = {
    "fashion": {"mood": "轻快时尚", "bpm_range": (110, 130), "instruments": "电子+吉他"},
    "beauty": {"mood": "清新温柔", "bpm_range": (80, 100), "instruments": "钢琴+弦乐"},
    "food": {"mood": "活泼欢快", "bpm_range": (120, 140), "instruments": "尤克里里+口哨"},
    "tech": {"mood": "科技感", "bpm_range": (90, 110), "instruments": "合成器+低音"},
    "home": {"mood": "温馨舒适", "bpm_range": (70, 90), "instruments": "原声吉他+钢琴"},
    "sport": {"mood": "热血动感", "bpm_range": (130, 150), "instruments": "鼓点+电子"},
    "mother_baby": {"mood": "温暖柔和", "bpm_range": (60, 80), "instruments": "音乐盒+竖琴"},
    "default": {"mood": "轻快正能量", "bpm_range": (100, 120), "instruments": "流行乐"},
}

# ── 导出预设 ──

EXPORT_PRESETS = {
    "douyin": {
        "format": "mp4",
        "video_codec": "libx264",
        "audio_codec": "aac",
        "resolution": "1080x1920",
        "fps": 30,
        "video_bitrate": "10M",
        "audio_bitrate": "192k",
        "movflags": "+faststart",  # 网络流式播放优化
    },
    "kuaishou": {
        "format": "mp4",
        "video_codec": "libx264",
        "audio_codec": "aac",
        "resolution": "1080x1920",
        "fps": 30,
        "video_bitrate": "10M",
        "audio_bitrate": "192k",
        "movflags": "+faststart",
    },
}


def get_ffmpeg_output_args(platform: str = "douyin") -> list[str]:
    """返回FFmpeg输出参数列表。"""
    preset = EXPORT_PRESETS.get(platform, EXPORT_PRESETS["douyin"])
    return [
        "-c:v", preset["video_codec"],
        "-b:v", preset["video_bitrate"],
        "-r", str(preset["fps"]),
        "-s", preset["resolution"],
        "-c:a", preset["audio_codec"],
        "-b:a", preset["audio_bitrate"],
        "-pix_fmt", "yuv420p",
        "-movflags", preset["movflags"],
    ]
