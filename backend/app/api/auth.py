from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class LoginRequest(BaseModel):
    phone: str | None = None
    email: str | None = None
    password: str | None = None
    sms_code: str | None = None


class RegisterRequest(BaseModel):
    phone: str
    sms_code: str
    invite_code: str


@router.post("/login")
def login(req: LoginRequest):
    # TODO: implement real auth
    return {
        "success": True,
        "data": {"access_token": "mock-jwt-token", "user": {"id": "u001", "name": "测试用户", "credits": 3000}},
        "message": "登录成功",
        "error": None,
    }


@router.post("/register")
def register(req: RegisterRequest):
    return {
        "success": True,
        "data": {"access_token": "mock-jwt-token", "user": {"id": "u002", "name": "新用户", "credits": 3000}},
        "message": "注册成功，已赠送 3000 运营力",
        "error": None,
    }


@router.post("/send-sms")
def send_sms(phone: str):
    return {"success": True, "data": None, "message": "验证码已发送", "error": None}
