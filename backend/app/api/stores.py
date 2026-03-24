"""
Store management API — 多店铺管理。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.engine import get_db
from app.db.models import Store, PlatformCredential
from app.middleware.auth import get_current_user_id
from app.services.credential_vault import CredentialVault

router = APIRouter()


class StoreCreate(BaseModel):
    name: str
    platform: str
    store_url: str | None = None
    operation_mode: str = "review"  # "auto" | "review"


class StoreUpdate(BaseModel):
    name: str | None = None
    operation_mode: str | None = None
    approval_gates: dict | None = None
    risk_thresholds: dict | None = None


class CredentialSave(BaseModel):
    platform: str
    credential_type: str = "oauth"
    data: dict  # will be encrypted


@router.get("/list")
async def list_stores(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Store).where(Store.user_id == user_id).order_by(Store.created_at.desc())
    )
    stores = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "name": s.name,
                "platform": s.platform,
                "store_url": s.store_url,
                "operation_mode": s.operation_mode,
                "approval_gates": s.approval_gates,
                "risk_thresholds": s.risk_thresholds,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in stores
        ],
    }


@router.post("/create")
async def create_store(
    body: StoreCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    store = Store(
        user_id=user_id,
        name=body.name,
        platform=body.platform,
        store_url=body.store_url,
        operation_mode=body.operation_mode,
    )
    db.add(store)
    await db.flush()
    return {"success": True, "data": {"id": store.id}}


@router.patch("/{store_id}")
async def update_store(
    store_id: str,
    body: StoreUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    store = await db.get(Store, store_id)
    if not store or store.user_id != user_id:
        raise HTTPException(status_code=404, detail="店铺不存在")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(store, field, value)
    await db.flush()
    return {"success": True, "data": {"id": store.id}}


@router.delete("/{store_id}")
async def delete_store(
    store_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    store = await db.get(Store, store_id)
    if not store or store.user_id != user_id:
        raise HTTPException(status_code=404, detail="店铺不存在")

    store.status = "deleted"
    await db.flush()
    return {"success": True}


@router.post("/{store_id}/credential")
async def save_credential(
    store_id: str,
    body: CredentialSave,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    store = await db.get(Store, store_id)
    if not store or store.user_id != user_id:
        raise HTTPException(status_code=404, detail="店铺不存在")

    vault = CredentialVault()
    encrypted = vault.encrypt(body.data)

    # Upsert credential
    result = await db.execute(
        select(PlatformCredential).where(
            PlatformCredential.store_id == store_id,
            PlatformCredential.platform == body.platform,
        )
    )
    cred = result.scalar_one_or_none()
    if cred:
        cred.encrypted_data = encrypted
        cred.credential_type = body.credential_type
    else:
        cred = PlatformCredential(
            store_id=store_id,
            platform=body.platform,
            credential_type=body.credential_type,
            encrypted_data=encrypted,
        )
        db.add(cred)

    await db.flush()
    return {"success": True}
