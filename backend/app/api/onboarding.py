"""
Onboarding API — 新用户引导设置。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import Store, UserDNA
from app.middleware.auth import get_current_user_id

router = APIRouter()


class OnboardingData(BaseModel):
    platforms: list[str]
    risk_level: str = "balanced"  # conservative | balanced | aggressive
    categories: list[str] = []
    automation_level: str = "guided"  # full_auto | guided | manual_ai


# 自动化级别映射到 operation_mode
AUTOMATION_TO_MODE = {
    "full_auto": "auto",
    "guided": "review",
    "manual_ai": "review",
}


@router.post("/complete")
async def complete_onboarding(
    body: OnboardingData,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """完成新用户引导，创建默认店铺和用户偏好。"""
    operation_mode = AUTOMATION_TO_MODE.get(body.automation_level, "review")

    # 为每个选中的平台创建默认店铺
    store_ids = []
    for platform in body.platforms:
        store = Store(
            user_id=user_id,
            name=f"我的{_platform_name(platform)}店铺",
            platform=platform,
            operation_mode=operation_mode,
            risk_thresholds=_default_risk_thresholds(body.risk_level),
        )
        db.add(store)
        await db.flush()
        store_ids.append(store.id)

    # 创建/更新 UserDNA
    user_dna = UserDNA(
        user_id=user_id,
        store_profile={
            "platforms": body.platforms,
            "risk_level": body.risk_level,
            "automation_level": body.automation_level,
        },
        scout_preferences={
            "categories": body.categories,
        },
        content_preferences={},
    )
    db.add(user_dna)
    await db.flush()

    return {
        "success": True,
        "data": {
            "store_ids": store_ids,
            "operation_mode": operation_mode,
        },
    }


def _platform_name(platform: str) -> str:
    names = {
        "douyin": "抖音",
        "xiaohongshu": "小红书",
        "taobao": "淘宝",
        "pinduoduo": "拼多多",
        "wechat_mp": "公众号",
        "1688": "1688",
    }
    return names.get(platform, platform)


def _default_risk_thresholds(risk_level: str) -> dict:
    presets = {
        "conservative": {
            "max_daily_ai_cost": 5,
            "max_new_pipelines_per_day": 2,
            "min_margin_percent": 25,
            "max_ad_daily_budget": 0,
        },
        "balanced": {
            "max_daily_ai_cost": 10,
            "max_new_pipelines_per_day": 3,
            "min_margin_percent": 20,
            "max_ad_daily_budget": 0,
        },
        "aggressive": {
            "max_daily_ai_cost": 30,
            "max_new_pipelines_per_day": 5,
            "min_margin_percent": 15,
            "max_ad_daily_budget": 50,
        },
    }
    return presets.get(risk_level, presets["balanced"])
