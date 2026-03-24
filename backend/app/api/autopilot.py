"""
Autopilot settings API — 自动驾驶模块控制。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import Store
from app.middleware.auth import get_current_user_id

router = APIRouter()


class ModuleModeUpdate(BaseModel):
    module_id: str
    mode: str  # "auto" | "review"


class GlobalModeUpdate(BaseModel):
    mode: str  # "auto" | "review"


class AutopilotSettings(BaseModel):
    store_id: str
    global_mode: str = "review"
    modules: dict = {}  # { module_id: "auto" | "review" }


@router.get("/settings")
async def get_settings(
    store_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取自动驾驶设置。如果有 store_id，返回该店铺配置，否则返回默认。"""
    if store_id:
        store = await db.get(Store, store_id)
        if not store or store.user_id != user_id:
            raise HTTPException(status_code=404, detail="店铺不存在")

        approval_gates = store.approval_gates or {}
        operation_mode = store.operation_mode or "review"
    else:
        # 查找用户第一个店铺
        result = await db.execute(
            select(Store).where(Store.user_id == user_id, Store.status == "active").limit(1)
        )
        store = result.scalar_one_or_none()
        approval_gates = store.approval_gates if store else {}
        operation_mode = store.operation_mode if store else "review"

    # 默认模块配置
    default_modules = {
        "discovery": "auto",
        "evaluation": "auto",
        "sourcing": "review",
        "content": "review",
        "publishing": "auto",
        "customer_service": "auto",
        "analytics": "auto",
    }

    # 合并店铺自定义配置
    modules = {**default_modules, **approval_gates}

    return {
        "success": True,
        "data": {
            "store_id": store.id if store else None,
            "global_mode": operation_mode,
            "modules": modules,
        },
    }


@router.post("/global-mode")
async def set_global_mode(
    body: GlobalModeUpdate,
    store_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """设置全局自动/审核模式。"""
    if body.mode not in ("auto", "review"):
        raise HTTPException(status_code=400, detail="模式必须为 auto 或 review")

    stores = await _get_user_stores(user_id, store_id, db)
    for store in stores:
        store.operation_mode = body.mode
        # 更新所有模块为同一模式
        store.approval_gates = {
            k: body.mode for k in (store.approval_gates or {})
        }

    await db.flush()
    return {"success": True}


@router.post("/module-mode")
async def set_module_mode(
    body: ModuleModeUpdate,
    store_id: str | None = None,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """设置单个模块的自动/审核模式。"""
    if body.mode not in ("auto", "review"):
        raise HTTPException(status_code=400, detail="模式必须为 auto 或 review")

    stores = await _get_user_stores(user_id, store_id, db)
    for store in stores:
        gates = store.approval_gates or {}
        gates[body.module_id] = body.mode
        store.approval_gates = gates

    await db.flush()
    return {"success": True}


async def _get_user_stores(
    user_id: str, store_id: str | None, db: AsyncSession
) -> list[Store]:
    if store_id:
        store = await db.get(Store, store_id)
        if not store or store.user_id != user_id:
            raise HTTPException(status_code=404, detail="店铺不存在")
        return [store]

    result = await db.execute(
        select(Store).where(Store.user_id == user_id, Store.status == "active")
    )
    return list(result.scalars().all())
