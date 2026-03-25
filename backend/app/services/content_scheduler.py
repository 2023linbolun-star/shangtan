"""
内容排期调度器 — 自动编排每日/每周内容发布计划。

规则：
- 涨粉:带货 = 8:2
- 每天2-3条，间隔4小时以上
- 带货安排在周三和周末
- 连续种草不超2条，穿插非种草
- 发布时间随机偏移5-15分钟（避免机器人特征）
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal


@dataclass
class ScheduleSlot:
    """一个排期时间槽。"""
    date: str                           # "2026-03-26"
    time: str                           # "12:15"
    day_of_week: str                    # "周三"
    content_type: str                   # "info_gap" / "ranking" / "life_hack" / "3act_drama" / "xhs_review"
    category: Literal["growth", "selling"]
    platform: str                       # "douyin" / "xiaohongshu"
    style_id: str                       # 对应风格注册表ID
    notes: str = ""                     # 备注


@dataclass
class WeeklySchedule:
    """一周的内容排期。"""
    week_start: str                     # "2026-03-23"
    slots: list[ScheduleSlot] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# 发布时间窗口（黄金时段）
PUBLISH_WINDOWS = [
    ("07:30", "08:30"),   # 早高峰
    ("12:00", "13:00"),   # 午休
    ("18:00", "19:00"),   # 下班
    ("20:30", "22:00"),   # 晚间黄金
]

# 星期中文
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 涨粉内容池（按轮次循环）
GROWTH_STYLES = [
    ("douyin_info_gap", "信息差图文"),
    ("douyin_life_hack", "生活妙招"),
    ("douyin_ranking", "清单盘点"),
    ("douyin_info_gap", "信息差图文"),
    ("douyin_life_hack", "生活妙招"),
]

# 带货内容池
SELLING_STYLES_DOUYIN = [
    ("douyin_3act_drama", "3幕场景剧"),
    ("douyin_ranking", "带货清单"),
]

SELLING_STYLES_XHS = [
    ("xhs_review", "真人测评"),
    ("xhs_seeding", "闺蜜种草"),
]


def generate_weekly_schedule(
    week_start: datetime | None = None,
    daily_count: int = 2,
    platforms: list[str] | None = None,
    growth_ratio: float = 0.8,
) -> WeeklySchedule:
    """
    生成一周的内容排期。

    Args:
        week_start: 周一日期，None则用下周一
        daily_count: 每天发布数量（2-3）
        platforms: 目标平台列表
        growth_ratio: 涨粉内容占比（0-1）
    """
    if week_start is None:
        today = datetime.now()
        days_until_monday = (7 - today.weekday()) % 7 or 7
        week_start = today + timedelta(days=days_until_monday)

    platforms = platforms or ["douyin", "xiaohongshu"]
    daily_count = max(2, min(3, daily_count))

    schedule = WeeklySchedule(week_start=week_start.strftime("%Y-%m-%d"))
    growth_style_idx = 0

    # 统计
    stats = {"growth": 0, "selling": 0, "total": 0}

    for day_offset in range(7):
        current_date = week_start + timedelta(days=day_offset)
        weekday = current_date.weekday()  # 0=周一
        weekday_name = WEEKDAY_NAMES[weekday]

        # 确定今天的内容配比
        # 周三和周末多安排带货
        is_selling_day = weekday in (2, 5, 6)  # 周三、周六、周日

        slots_today = []

        for slot_idx in range(daily_count):
            # 决定这条是涨粉还是带货
            if is_selling_day and slot_idx == daily_count - 1:
                # 带货日的最后一条安排带货
                is_selling = True
            elif random.random() > growth_ratio:
                is_selling = True
            else:
                is_selling = False

            # 避免连续2条都是带货
            if len(slots_today) >= 1 and slots_today[-1].category == "selling" and is_selling:
                is_selling = False

            # 选择平台
            if is_selling and "xiaohongshu" in platforms and random.random() < 0.4:
                platform = "xiaohongshu"
            else:
                platform = "douyin" if "douyin" in platforms else platforms[0]

            # 选择风格
            if is_selling:
                if platform == "xiaohongshu":
                    style_id, style_name = random.choice(SELLING_STYLES_XHS)
                else:
                    style_id, style_name = random.choice(SELLING_STYLES_DOUYIN)
                category = "selling"
                stats["selling"] += 1
            else:
                style_id, style_name = GROWTH_STYLES[growth_style_idx % len(GROWTH_STYLES)]
                growth_style_idx += 1
                category = "growth"
                stats["growth"] += 1

            # 选择发布时间（从窗口中选+随机偏移）
            window = PUBLISH_WINDOWS[slot_idx % len(PUBLISH_WINDOWS)]
            base_hour, base_min = map(int, window[0].split(":"))
            offset_minutes = random.randint(5, 30)
            publish_time = f"{base_hour:02d}:{base_min + offset_minutes:02d}"

            slot = ScheduleSlot(
                date=current_date.strftime("%Y-%m-%d"),
                time=publish_time,
                day_of_week=weekday_name,
                content_type=style_name,
                category=category,
                platform=platform,
                style_id=style_id,
            )
            slots_today.append(slot)
            stats["total"] += 1

        schedule.slots.extend(slots_today)

    schedule.summary = {
        "total": stats["total"],
        "growth": stats["growth"],
        "selling": stats["selling"],
        "growth_ratio": round(stats["growth"] / max(stats["total"], 1) * 100),
        "daily_average": round(stats["total"] / 7, 1),
    }

    return schedule


def schedule_to_dict(schedule: WeeklySchedule) -> dict:
    """将排期转换为可序列化的dict。"""
    return {
        "week_start": schedule.week_start,
        "summary": schedule.summary,
        "slots": [
            {
                "date": s.date,
                "time": s.time,
                "day_of_week": s.day_of_week,
                "content_type": s.content_type,
                "category": s.category,
                "platform": s.platform,
                "style_id": s.style_id,
                "notes": s.notes,
            }
            for s in schedule.slots
        ],
    }
