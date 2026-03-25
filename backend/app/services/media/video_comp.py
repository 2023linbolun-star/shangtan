"""
FFmpeg 视频合成服务

将图片序列 + 配音 + 字幕 + BGM 合成为抖音竖屏视频。
使用 Ken Burns 效果（缓慢缩放+平移）让静态图片产生动感。

依赖：系统需安装 ffmpeg
"""

import asyncio
import json
import logging
import os
import uuid

from app.services.experts.video_specs import (
    DOUYIN_VIDEO, SUBTITLE, AUDIO, KEN_BURNS, EXPORT_PRESETS, get_ffmpeg_output_args,
)

logger = logging.getLogger("shangtanai.media.video_comp")


async def _run_ffmpeg(args: list[str], timeout: int = 300) -> bool:
    """执行ffmpeg命令。"""
    cmd = ["ffmpeg", "-y"] + args
    logger.info(f"FFmpeg cmd: {' '.join(cmd[:20])}...")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

    if proc.returncode != 0:
        logger.error(f"FFmpeg failed (code {proc.returncode}): {stderr.decode()[-500:]}")
        return False
    return True


def _build_ken_burns_filter(
    image_path: str,
    duration: float,
    index: int,
    width: int = 1080,
    height: int = 1920,
) -> str:
    """
    为单张图片生成 Ken Burns 效果的 filtergraph。
    交替使用 zoom-in 和 pan 效果。
    """
    fps = DOUYIN_VIDEO["fps"]
    total_frames = int(duration * fps)
    zoom_start, zoom_end = KEN_BURNS["zoom_range"]

    if index % 2 == 0:
        # 偶数场景：缩放效果
        zoom_expr = f"{zoom_start}+({zoom_end}-{zoom_start})*on/{total_frames}"
        x_expr = f"iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)"
    else:
        # 奇数场景：平移效果（从左到右）
        zoom_expr = f"{zoom_end}"
        pan_pixels = int(KEN_BURNS["pan_speed"] * duration)
        x_expr = f"{pan_pixels}*on/{total_frames}"
        y_expr = f"ih/2-(ih/zoom/2)"

    return (
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
        f":d={total_frames}:s={width}x{height}:fps={fps}"
    )


async def generate_srt(
    scenes: list[dict],
    output_path: str,
) -> str:
    """
    从脚本场景生成 SRT 字幕文件。

    Args:
        scenes: [{"scene_number": 1, "voiceover": "文案", "duration_ms": 3000}, ...]
        output_path: SRT文件保存路径
    """
    srt_lines = []
    current_time_ms = 0

    for i, scene in enumerate(scenes):
        text = scene.get("voiceover", "").strip()
        if not text:
            current_time_ms += scene.get("duration_ms", 3000)
            continue

        duration_ms = scene.get("duration_ms", 3000)

        # 按标点拆分长文案为多条字幕
        segments = _split_subtitle_text(text)

        segment_duration = duration_ms / max(len(segments), 1)

        for j, segment in enumerate(segments):
            start_ms = current_time_ms + int(j * segment_duration)
            end_ms = start_ms + int(segment_duration)

            # 提前显示
            lead_ms = int(SUBTITLE["lead_time"] * 1000)
            start_ms = max(0, start_ms - lead_ms)

            srt_lines.append(str(i * 10 + j + 1))
            srt_lines.append(f"{_ms_to_srt_time(start_ms)} --> {_ms_to_srt_time(end_ms)}")
            srt_lines.append(segment)
            srt_lines.append("")

        current_time_ms += duration_ms

    srt_content = "\n".join(srt_lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return output_path


def _split_subtitle_text(text: str, max_chars: int = 18) -> list[str]:
    """按标点和长度拆分字幕文本，每行不超过max_chars字。"""
    # 先按标点拆
    import re
    raw_segments = re.split(r'[，。！？；、,.\!\?;]', text)
    raw_segments = [s.strip() for s in raw_segments if s.strip()]

    # 再检查长度
    result = []
    for seg in raw_segments:
        if len(seg) <= max_chars:
            result.append(seg)
        else:
            # 强制拆分
            for k in range(0, len(seg), max_chars):
                chunk = seg[k:k + max_chars]
                if chunk:
                    result.append(chunk)
    return result if result else [text[:max_chars]]


def _ms_to_srt_time(ms: int) -> str:
    """毫秒转SRT时间格式 HH:MM:SS,mmm。"""
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    remaining = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{remaining:03d}"


async def compose_video(
    scene_images: list[str],
    scene_audios: list[str],
    scene_durations: list[float],
    srt_path: str | None = None,
    bgm_path: str | None = None,
    output_dir: str | None = None,
    platform: str = "douyin",
) -> dict:
    """
    将图片+配音+字幕+BGM合成为完整视频。

    Args:
        scene_images: 每个场景的图片路径列表
        scene_audios: 每个场景的配音文件路径列表
        scene_durations: 每个场景的持续时长（秒）
        srt_path: 字幕文件路径
        bgm_path: 背景音乐路径
        output_dir: 输出目录
        platform: 目标平台

    Returns:
        {"video_path": "...", "duration": 45.0, "file_size_mb": 12.3}
    """
    output_dir = output_dir or os.path.join("storage/assets/videos", str(uuid.uuid4())[:8])
    os.makedirs(output_dir, exist_ok=True)

    width = DOUYIN_VIDEO["width"]
    height = DOUYIN_VIDEO["height"]
    fps = DOUYIN_VIDEO["fps"]
    transition = KEN_BURNS["transition_duration"]

    # Step 1: 为每个场景生成带 Ken Burns 效果的视频片段
    scene_clips = []
    for i, (img_path, duration) in enumerate(zip(scene_images, scene_durations)):
        if not img_path or not os.path.exists(img_path):
            logger.warning(f"Scene {i}: image not found at {img_path}, skipping")
            continue

        clip_path = os.path.join(output_dir, f"clip_{i:02d}.mp4")
        kb_filter = _build_ken_burns_filter(img_path, duration, i, width, height)

        args = [
            "-loop", "1",
            "-i", img_path,
            "-vf", kb_filter,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            clip_path,
        ]

        success = await _run_ffmpeg(args)
        if success:
            scene_clips.append(clip_path)

    if not scene_clips:
        logger.error("No scene clips generated")
        return {"video_path": "", "duration": 0, "file_size_mb": 0}

    # Step 2: 拼接所有场景片段（带交叉淡入淡出）
    concat_path = os.path.join(output_dir, "concat.mp4")
    concat_list_path = os.path.join(output_dir, "concat_list.txt")

    with open(concat_list_path, "w") as f:
        for clip in scene_clips:
            f.write(f"file '{clip}'\n")

    args = [
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        concat_path,
    ]
    await _run_ffmpeg(args)

    # Step 3: 合并配音
    mixed_path = os.path.join(output_dir, "with_voice.mp4")

    # 先把所有配音拼接成一个完整音频
    voice_list_path = os.path.join(output_dir, "voice_list.txt")
    valid_audios = [a for a in scene_audios if a and os.path.exists(a)]

    if valid_audios:
        with open(voice_list_path, "w") as f:
            for audio in valid_audios:
                f.write(f"file '{audio}'\n")

        voice_concat_path = os.path.join(output_dir, "voice_full.mp3")
        await _run_ffmpeg([
            "-f", "concat", "-safe", "0",
            "-i", voice_list_path,
            "-c:a", "libmp3lame",
            voice_concat_path,
        ])

        # 混合视频和配音
        voice_db = AUDIO["voice_db_range"][0]  # -12dB
        await _run_ffmpeg([
            "-i", concat_path,
            "-i", voice_concat_path,
            "-c:v", "copy",
            "-c:a", AUDIO["codec"],
            "-b:a", AUDIO["bitrate"],
            "-shortest",
            mixed_path,
        ])
    else:
        mixed_path = concat_path

    # Step 4: 叠加BGM
    bgm_mixed_path = os.path.join(output_dir, "with_bgm.mp4")
    if bgm_path and os.path.exists(bgm_path):
        bgm_db = AUDIO["bgm_db"]
        fade_in = AUDIO["bgm_fade_in"]
        fade_out = AUDIO["bgm_fade_out"]

        # 获取视频时长
        total_duration = sum(scene_durations)

        await _run_ffmpeg([
            "-i", mixed_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[1:a]afade=t=in:st=0:d={fade_in},afade=t=out:st={total_duration-fade_out}:d={fade_out},"
            f"volume={bgm_db}dB[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", AUDIO["codec"],
            "-b:a", AUDIO["bitrate"],
            bgm_mixed_path,
        ])
        mixed_path = bgm_mixed_path

    # Step 5: 叠加字幕
    final_path = os.path.join(output_dir, "final.mp4")
    if srt_path and os.path.exists(srt_path):
        font_name = SUBTITLE["fonts"][0]
        font_size = SUBTITLE["font_size"]
        margin_v = int(height * SUBTITLE["margin_bottom_pct"])

        # FFmpeg字幕样式
        style = (
            f"FontName={font_name},"
            f"FontSize={font_size},"
            f"PrimaryColour=&HFFFFFF&,"
            f"OutlineColour=&H000000&,"
            f"Outline={SUBTITLE['stroke_width']},"
            f"Shadow=0,"
            f"MarginV={margin_v}"
        )

        await _run_ffmpeg([
            "-i", mixed_path,
            "-vf", f"subtitles={srt_path}:force_style='{style}'",
            *get_ffmpeg_output_args(platform),
            final_path,
        ])
    else:
        # 无字幕，直接导出最终格式
        await _run_ffmpeg([
            "-i", mixed_path,
            *get_ffmpeg_output_args(platform),
            final_path,
        ])

    # 计算文件信息
    file_size_mb = 0
    duration = sum(scene_durations)
    if os.path.exists(final_path):
        file_size_mb = round(os.path.getsize(final_path) / 1024 / 1024, 1)

    logger.info(f"Video composed: {duration}s, {file_size_mb}MB → {final_path}")

    # 清理中间文件
    for tmp in scene_clips + [concat_path, concat_list_path, voice_list_path]:
        if isinstance(tmp, str) and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

    return {
        "video_path": final_path,
        "duration": duration,
        "file_size_mb": file_size_mb,
    }
