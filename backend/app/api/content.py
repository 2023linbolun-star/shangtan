"""内容工厂 API — AI内容生成 + 风格选择 + 偏好管理"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User, GeneratedContent, Product, UserDNA
from app.middleware.auth import get_current_user, get_optional_user
from app.services.ai_engine import ai_analyze_full
from app.services.prompts import content_douyin, content_xiaohongshu, content_taobao, content_pdd
from app.services.violation_checker import check_violations
from app.services.styles.registry import list_styles, get_style, STYLE_REGISTRY

router = APIRouter()

# Platform -> (prompt_module, task_type)
PLATFORM_PROMPTS = {
    "douyin": (content_douyin, "content_social"),
    "xiaohongshu": (content_xiaohongshu, "content_social"),
    "kuaishou": (content_douyin, "content_social"),
    "taobao": (content_taobao, "content_formal"),
    "tmall": (content_taobao, "content_formal"),
    "pinduoduo": (content_pdd, "content_formal"),
}


# ══════════════════════════════════════════════════════════════
#  内容生成
# ══════════════════════════════════════════════════════════════

class ContentGenerateRequest(BaseModel):
    content_type: str = "auto"
    product_info: str = ""
    product_id: str | None = None
    platform: str = "douyin"
    style: str = "种草"
    style_id: str | None = None  # 新增：指定风格模板
    notes: str = ""


@router.post("/generate")
async def generate_content(
    req: ContentGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate platform-specific content using AI."""
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

    # 加载用户偏好
    user_prefs = await _get_user_preferences(db, user.id)

    # 确定风格
    style_config = None
    if req.style_id:
        style_config = get_style(req.style_id)

    # 获取prompt模块和task_type
    if style_config:
        prompt_module, task_type = PLATFORM_PROMPTS.get(
            req.platform, (content_douyin, "content_social")
        )
        task_type = style_config.task_type
    else:
        prompt_module, task_type = PLATFORM_PROMPTS.get(
            req.platform, (content_douyin, "content_social")
        )

    prompt = prompt_module.build_prompt(
        product_info=product_info,
        style=req.style,
        notes=req.notes,
    )

    # 注入用户偏好到prompt
    if user_prefs:
        pref_injection = _build_preference_injection(user_prefs)
        if pref_injection:
            prompt = prompt + pref_injection

    # 记录应用了哪些偏好（归因流）
    applied_prefs = _get_applied_preferences(user_prefs)

    result = await ai_analyze_full(
        prompt,
        task_type=task_type,
        system=prompt_module.SYSTEM,
    )

    violation_result = check_violations(result["text"], platform=req.platform)

    content_record = GeneratedContent(
        product_id=req.product_id or "",
        content_type=req.content_type,
        platform=req.platform,
        content={
            "raw": result["text"],
            "violation_check": violation_result,
            "style_id": req.style_id or "",
            "applied_preferences": applied_prefs,
        },
        ai_model=result["model"],
        credits_used=max(1, int(result["cost"] * 10000)),
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
            "style_id": req.style_id,
            "applied_preferences": applied_prefs,
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


# ══════════════════════════════════════════════════════════════
#  反馈 + 学习
# ══════════════════════════════════════════════════════════════

class FeedbackRequest(BaseModel):
    vote: int  # 1=👍, -1=👎
    edit_notes: str | None = None  # 用户修改意见


@router.post("/{content_id}/feedback")
async def content_feedback(
    content_id: str,
    req: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback and trigger preference learning."""
    result = await db.execute(select(GeneratedContent).where(GeneratedContent.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")

    content.feedback = req.vote
    await db.flush()

    # 触发偏好学习
    from app.agents.memory import MemoryStore
    store = MemoryStore(db)
    learned = await store.learn_from_feedback(
        user_id=user.id,
        agent_type=f"content_{content.platform}",
        content_text=content.content.get("raw", "") if isinstance(content.content, dict) else str(content.content),
        feedback_score=req.vote,
        edit_notes=req.edit_notes,
    )

    return {
        "success": True,
        "data": {"learned": learned},
        "message": "反馈已记录，AI已学习",
        "error": None,
    }


# ══════════════════════════════════════════════════════════════
#  风格管理
# ══════════════════════════════════════════════════════════════

@router.get("/styles")
async def get_styles(
    platform: str | None = None,
    category: str | None = None,
    user: User = Depends(get_optional_user),
):
    """列出所有可用风格模板。"""
    styles = list_styles(platform=platform, category=category)
    return {
        "success": True,
        "data": {
            "styles": [
                {
                    "id": s.id,
                    "name": s.name,
                    "platform": s.platform,
                    "category": s.category,
                    "description": s.description,
                    "tags": s.tags,
                    "customizable_fields": s.customizable_fields,
                    "default_params": s.default_params,
                }
                for s in styles
            ]
        },
        "message": "ok",
        "error": None,
    }


class StyleSelectRequest(BaseModel):
    platform: str
    style_id: str


@router.post("/styles/select")
async def select_style(
    req: StyleSelectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户选择某平台的默认风格。"""
    style = get_style(req.style_id)
    if not style:
        raise HTTPException(status_code=404, detail=f"风格 {req.style_id} 不存在")

    from app.agents.memory import MemoryStore
    store = MemoryStore(db)
    await store.update_user_dna(user.id, {
        "content_preferences": {
            "preferred_styles": {req.platform: req.style_id}
        }
    })

    return {
        "success": True,
        "data": {"platform": req.platform, "style_id": req.style_id, "style_name": style.name},
        "message": f"已将 {req.platform} 默认风格设为「{style.name}」",
        "error": None,
    }


# ══════════════════════════════════════════════════════════════
#  用户偏好
# ══════════════════════════════════════════════════════════════

class PreferencesUpdateRequest(BaseModel):
    voice_style: str | None = None
    visual_preference: str | None = None
    hook_preference: str | None = None
    content_length: str | None = None
    emoji_usage: str | None = None
    humor_level: str | None = None
    selling_intensity: str | None = None
    avoid_patterns: list[str] | None = None
    category_overrides: dict | None = None


@router.get("/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户当前偏好设置。"""
    prefs = await _get_user_preferences(db, user.id)
    return {
        "success": True,
        "data": {"preferences": prefs},
        "message": "ok",
        "error": None,
    }


@router.post("/preferences")
async def update_preferences(
    req: PreferencesUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """用户主动设置偏好。"""
    from app.agents.memory import MemoryStore
    store = MemoryStore(db)

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if updates:
        await store.update_user_dna(user.id, updates)

    return {
        "success": True,
        "data": {"updated_fields": list(updates.keys())},
        "message": f"已更新 {len(updates)} 项偏好设置",
        "error": None,
    }


# ══════════════════════════════════════════════════════════════
#  AI记忆统计（记忆面板数据）
# ══════════════════════════════════════════════════════════════

@router.get("/agent/memory-stats")
async def get_memory_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取AI记忆统计——记忆面板展示数据。"""
    from app.agents.memory import MemoryStore
    store = MemoryStore(db)
    stats = await store.get_memory_stats(user.id)
    return {
        "success": True,
        "data": stats,
        "message": "ok",
        "error": None,
    }


@router.get("/assets")
async def list_assets(user: User = Depends(get_current_user)):
    """Asset library — placeholder for future file storage."""
    return {"success": True, "data": {"assets": []}, "message": "ok", "error": None}


# ══════════════════════════════════════════════════════════════
#  内部工具函数
# ══════════════════════════════════════════════════════════════

async def _get_user_preferences(db: AsyncSession, user_id: str) -> dict:
    """加载用户偏好。"""
    result = await db.execute(select(UserDNA).where(UserDNA.user_id == user_id))
    dna = result.scalar_one_or_none()
    if not dna:
        return {}
    return dna.content_preferences or {}


def _build_preference_injection(prefs: dict) -> str:
    """将用户偏好构建为 prompt 注入片段。"""
    if not prefs:
        return ""

    lines = ["\n## 用户个人偏好（必须遵循）"]
    field_labels = {
        "voice_style": "语气风格",
        "visual_preference": "视觉风格",
        "hook_preference": "开头偏好",
        "content_length": "内容长度",
        "emoji_usage": "emoji使用",
        "humor_level": "幽默程度",
        "selling_intensity": "推销强度",
    }

    added = False
    for key, label in field_labels.items():
        val = prefs.get(key)
        if val:
            lines.append(f"- {label}: {val}")
            added = True

    avoid = prefs.get("avoid_patterns", [])
    if avoid:
        lines.append("\n### 明确避免")
        for a in avoid:
            lines.append(f"- ⚠️ 不要: {a}")
        added = True

    return "\n".join(lines) if added else ""


def _get_applied_preferences(prefs: dict) -> list[str]:
    """提取实际应用了哪些偏好（用于归因流展示）。"""
    applied = []
    if prefs.get("voice_style"):
        applied.append(f"语气风格: {prefs['voice_style']}")
    if prefs.get("visual_preference"):
        applied.append(f"视觉风格: {prefs['visual_preference']}")
    if prefs.get("hook_preference"):
        applied.append(f"开头偏好: {prefs['hook_preference']}")
    if prefs.get("selling_intensity"):
        applied.append(f"推销强度: {prefs['selling_intensity']}")
    if prefs.get("avoid_patterns"):
        applied.append(f"回避模式: {len(prefs['avoid_patterns'])}条")
    if prefs.get("preferred_styles"):
        for p, s in prefs["preferred_styles"].items():
            applied.append(f"{p}默认风格: {s}")
    return applied
