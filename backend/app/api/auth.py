from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User, CreditTransaction
from app.middleware.auth import hash_password, verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    password: str = ""


class RegisterRequest(BaseModel):
    phone: str
    password: str
    invite_code: str = ""


def _user_response(user: User, token: str) -> dict:
    return {
        "success": True,
        "data": {
            "access_token": token,
            "user": {"id": user.id, "name": user.name, "phone": user.phone, "credits": user.credits},
        },
        "message": "ok",
        "error": None,
    }


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    if req.phone:
        result = await db.execute(select(User).where(User.phone == req.phone))
    elif req.email:
        result = await db.execute(select(User).where(User.email == req.email))
    else:
        raise HTTPException(status_code=400, detail="请提供手机号或邮箱")

    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")

    token = create_access_token(user.id)
    return _user_response(user, token)


@router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if phone already registered
    existing = await db.execute(select(User).where(User.phone == req.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(
        phone=req.phone,
        password_hash=hash_password(req.password),
        name=f"用户{req.phone[-4:]}",
        credits=3000,
    )
    db.add(user)
    await db.flush()  # Generate user.id first

    # Record signup bonus
    tx = CreditTransaction(
        user_id=user.id,
        amount=3000,
        operation="register_bonus",
        detail="注册赠送 3000 运营力",
    )
    db.add(tx)
    await db.flush()

    token = create_access_token(user.id)
    return _user_response(user, token)
