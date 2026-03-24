"""内容工厂 API — 真实 AI 内容生成"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User, GeneratedContent, Product
from app.middleware.auth import get_current_user, get_optional_user
from app.services.ai_engine import ai_analyze_full
from app.services.prompts import content_douyin, content_xiaohongshu, content_taobao, content_pdd
from app.services.violation_checker import check_violations

router = APIRouter()

# Platform -> (prompt_module, task_type)
PLATFORM_PROMPTS = {
    "douyin": (content_douyin, "content_social"),
    "xiaohongshu": (content_xiaohongshu, "content_social"),
    "kuaishou": (content_douyin, "content_social"),  # 快手复用抖音模板，风格调整
    "taobao": (content_taobao, "content_formal"),
    "tmall": (content_taobao, "content_formal"),
    "pinduoduo": (content_pdd, "content_formal"),
}


class ContentGenerateRequest(BaseModel):
    content_type: str = "auto"  # auto, video_script, note, product_copy
    product_info: str = ""      # 产品描述（手动输入）
    product_id: str | None = None  # 或从数据库读取
    platform: str = "douyin"
    style: str = "种草"
    notes: str = ""


@router.post("/generate")
async def generate_content(
    req: ContentGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate platform-specific content using AI."""
    # Get product info
    product_info = req.product_info
    if req.product_id and not product_info:
        result = await db.execute(
            select(Product).where(Product.id == req.product_id, Product.user_id == user.id)
        )
        product = result.scalar_one_or_none()
        if product:
            product_info = f"品名：{product.title}\n价格：¥{product.price}\n平台：{product.platform}\n关键词：{product.keyword}"

    if not product_info:
        raise HTTPException(status_code=400, detail="请提供产品信息或选择已有产品")

    # Get platform-specific prompt
    prompt_module, task_type = PLATFORM_PROMPTS.get(
        req.platform, (content_douyin, "content_social")
    )

    prompt = prompt_module.build_prompt(
        product_info=product_info,
        style=req.style,
        notes=req.notes,
    )

    # Call AI
    result = await ai_analyze_full(
        prompt,
        task_type=task_type,
        system=prompt_module.SYSTEM,
    )

    # Violation check on generated content
    violation_result = check_violations(
        result["text"],
        platform=req.platform,
    )

    # Save to database
    content_record = GeneratedContent(
        product_id=req.product_id or "",
        content_type=req.content_type,
        platform=req.platform,
        content={
            "raw": result["text"],
            "violation_check": violation_result,
        },
        ai_model=result["model"],
        credits_used=max(1, int(result["cost"] * 10000)),  # Rough credit mapping
    )
    db.add(content_record)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": content_record.id,
            "type": req.content_type,
            "platform": req.platform,
            "content": result["text"],
            "violation_check": violation_result,
            "ai_model": result["model"],
            "credits_used": content_record.credits_used,
            "cost_usd": round(result["cost"], 6),
        },
        "message": "生成完成",
        "error": None,
    }


@router.get("/list")
async def list_contents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's generated contents."""
    result = await db.execute(
        select(GeneratedContent)
        .join(Product, GeneratedContent.product_id == Product.id, isouter=True)
        .where(Product.user_id == user.id)
        .order_by(GeneratedContent.created_at.desc())
        .limit(50)
    )
    contents = result.scalars().all()

    return {
        "success": True,
        "data": {
            "contents": [
                {
                    "id": c.id,
                    "type": c.content_type,
                    "platform": c.platform,
                    "content": c.content,
                    "ai_model": c.ai_model,
                    "status": c.status.value,
                    "feedback": c.feedback,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in contents
            ]
        },
        "message": "ok",
        "error": None,
    }


@router.post("/{content_id}/feedback")
async def content_feedback(
    content_id: str,
    vote: int,  # 1=thumbs up, -1=thumbs down
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback on generated content quality."""
    result = await db.execute(select(GeneratedContent).where(GeneratedContent.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    content.feedback = vote
    await db.flush()

    return {"success": True, "data": None, "message": "反馈已记录", "error": None}


@router.get("/assets")
async def list_assets(user: User = Depends(get_current_user)):
    """Asset library — placeholder for future file storage."""
    return {"success": True, "data": {"assets": []}, "message": "ok", "error": None}
