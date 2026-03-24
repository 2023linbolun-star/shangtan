"""
Feedback API — 用户反馈 + User DNA 查看。
驱动 Agent 自我进化系统。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User
from app.middleware.auth import get_current_user
from app.agents.learning import LearningEngine
from app.agents.memory import MemoryStore

router = APIRouter()


class FeedbackRequest(BaseModel):
    memory_id: str
    score: int  # -1, 0, 1
    edits: dict | None = None
    original_output: dict | None = None
    feedback_text: str | None = None


@router.post("/submit")
async def submit_feedback(
    req: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交反馈，触发 Agent 学习。"""
    engine = LearningEngine(db)
    await engine.process_feedback(
        user_id=user.id,
        memory_id=req.memory_id,
        feedback_score=req.score,
        user_edits=req.edits,
        original_output=req.original_output,
        feedback_text=req.feedback_text,
    )
    return {
        "success": True,
        "data": None,
        "message": "反馈已记录，AI 正在学习",
        "error": None,
    }


@router.get("/dna")
async def get_user_dna(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看系统学习到的用户画像。"""
    store = MemoryStore(db)
    dna = await store.get_user_dna(user.id)
    return {
        "success": True,
        "data": dna,
        "message": "ok",
        "error": None,
    }


@router.post("/dna/update")
async def update_user_dna(
    updates: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动更新用户画像（用户主动设置偏好）。"""
    store = MemoryStore(db)
    await store.update_user_dna(user.id, updates)
    return {
        "success": True,
        "data": None,
        "message": "用户画像已更新",
        "error": None,
    }
