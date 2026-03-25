"""内容工厂 API — AI内容生成 + 风格选择 + 偏好管理"""

import logging
import os
import uuid as uuid_mod
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User, GeneratedContent, Product, UserDNA, Asset, AssetCategory
from app.middleware.auth import get_current_user, get_optional_user
from app.core.config import ASSETS_DIR
from app.services.ai_engine import ai_analyze_full
from app.services.prompts import content_douyin, content_xiaohongshu, content_taobao, content_pdd
from app.services.violation_checker import check_violations
from app.services.styles.registry import list_styles, get_style, STYLE_REGISTRY

logger = logging.getLogger("shangtanai.api.content")

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
    asset_ids: list[str] | None = None  # 附加素材ID列表
    modification_instruction: str | None = None  # 迭代修改指令
    original_content: str | None = None  # 迭代修改的原内容


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

    # 注入素材引用
    if req.asset_ids:
        prompt += f"\n\n## 参考素材\n已附加 {len(req.asset_ids)} 个素材文件，请在内容中融入这些视觉元素。素材ID: {', '.join(req.asset_ids)}"

    # 迭代修改模式
    if req.modification_instruction and req.original_content:
        prompt = f"请根据以下修改要求，修改原有内容。\n\n## 原内容\n{req.original_content}\n\n## 修改要求\n{req.modification_instruction}\n\n## 原始产品信息\n{product_info}"

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
            "asset_ids": req.asset_ids,
            "is_modification": bool(req.modification_instruction),
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


# ══════════════════════════════════════════════════════════════
#  AI智能方案
# ══════════════════════════════════════════════════════════════

class SmartPlanRequest(BaseModel):
    product_info: str
    product_id: str | None = None
    budget_hint: str | None = None
    focus_type: str | None = None  # None=全局, "short_video"/"xhs_note"/"product_main_image"/"promo_video"/"ecommerce"


@router.post("/smart-plan")
async def generate_smart_plan(
    req: SmartPlanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI分析商品，生成内容营销方案。"""
    import json as json_mod
    from app.services.prompts.smart_plan import build_prompt, SYSTEM
    from app.services.styles.registry import list_styles

    # Load user preferences
    user_prefs = await _get_user_preferences(db, user.id)

    # Get available styles (filter by focus if needed)
    all_styles = list_styles()
    styles_data = [
        {"id": s.id, "name": s.name, "platform": s.platform, "description": s.description}
        for s in all_styles
    ]

    # Build prompt
    prompt = build_prompt(
        product_info=req.product_info,
        available_styles=styles_data,
        user_prefs=user_prefs,
        focus_type=req.focus_type,
    )

    # Call AI (strategy task -> Claude)
    try:
        result = await ai_analyze_full(prompt, task_type="strategy", system=SYSTEM)
        ai_text = result.get("text", "")
        ai_model = result.get("model", "unknown")
        ai_cost = result.get("cost", 0)

        # Parse JSON from response
        # Try to extract JSON from the response (might have markdown fences)
        json_str = ai_text.strip()
        if json_str.startswith("```"):
            json_str = json_str.split("```")[1]
            if json_str.startswith("json"):
                json_str = json_str[4:]
        json_str = json_str.strip()

        plan_data = json_mod.loads(json_str)
    except Exception as e:
        # Fallback to rule-based plan
        plan_data = _fallback_plan(req.product_info, req.focus_type)
        ai_model = "rule_engine"
        ai_cost = 0

    return {
        "success": True,
        "data": {
            "plan": plan_data,
            "focus_type": req.focus_type,
            "ai_model": ai_model,
            "cost_usd": round(ai_cost, 6),
        },
        "message": "方案生成完成",
        "error": None,
    }


def _fallback_plan(product_info: str, focus_type: str | None) -> dict:
    """规则引擎降级方案。"""
    info_lower = product_info.lower()

    # Simple heuristics
    is_fashion = any(kw in info_lower for kw in ["衣", "裤", "裙", "鞋", "帽", "包"])
    is_beauty = any(kw in info_lower for kw in ["防晒", "护肤", "面膜", "口红", "美妆"])
    is_home = any(kw in info_lower for kw in ["厨房", "收纳", "清洁", "家居"])
    is_tech = any(kw in info_lower for kw in ["充电", "耳机", "手机", "数码", "风扇"])

    if focus_type == "short_video":
        style = "douyin_3act_drama" if is_fashion or is_beauty else "douyin_seeding"
        return {
            "platform": "douyin",
            "recommended_style_id": style,
            "recommended_style_name": "3幕场景剧" if "3act" in style else "种草推荐",
            "reason": "该品类在抖音短视频转化率较高",
            "params": {"duration": 20, "hook_type": "冲突反差", "selling_intensity": "软种草"},
        }

    elif focus_type == "xhs_note":
        style = "xhs_review" if is_beauty or is_fashion else "xhs_seeding"
        return {
            "recommended_style_id": style,
            "recommended_style_name": "真人测评" if "review" in style else "闺蜜种草",
            "reason": "该品类适合小红书种草",
            "params": {"tone": "测评" if "review" in style else "闺蜜", "image_style": "真人手机拍", "word_count": 800},
        }

    elif focus_type == "product_main_image":
        styles = ["white_bg", "scene", "selling_point"]
        with_model = is_fashion or is_beauty
        if with_model:
            styles.append("model")
        return {
            "recommended_styles": styles,
            "with_model": with_model,
            "reason": "标准电商主图方案" + ("，服饰类建议加模特展示" if with_model else ""),
            "model_params": {"gender": "female", "age_range": "20-25", "style": "时尚"} if with_model else None,
        }

    elif focus_type == "promo_video":
        return {
            "duration": 15,
            "voice": "female_active",
            "with_model": is_fashion,
            "reason": "15秒适合商品详情页展示",
            "video_style": "产品展示",
        }

    elif focus_type == "ecommerce":
        return {
            "platform": "taobao",
            "recommended_style_id": "listing_taobao",
            "recommended_style_name": "淘宝商品文案",
            "reason": "标准电商Listing方案",
            "params": {"title_style": "关键词密集", "selling_points_count": 5},
        }

    else:
        # Global plan
        plans = [
            {
                "platform": "douyin",
                "priority": 1,
                "reason": "短视频是当前最大流量入口",
                "content_items": [
                    {"content_type": "short_video", "style_id": "douyin_3act_drama", "style_name": "3幕场景剧", "params": {"duration": 20}},
                ],
                "main_images": [],
                "needs_video": False,
                "video_params": None,
            },
        ]
        if is_beauty or is_fashion:
            plans.append({
                "platform": "xiaohongshu",
                "priority": 2,
                "reason": "该品类适合小红书种草",
                "content_items": [
                    {"content_type": "xhs_note", "style_id": "xhs_review", "style_name": "真人测评", "params": {}},
                ],
                "main_images": [],
                "needs_video": False,
                "video_params": None,
            })
        plans.append({
            "platform": "taobao",
            "priority": 3 if len(plans) > 1 else 2,
            "reason": "需要电商平台商品页面",
            "content_items": [
                {"content_type": "ecommerce", "style_id": "listing_taobao", "style_name": "淘宝商品文案", "params": {}},
            ],
            "main_images": ["white_bg", "scene", "selling_point"],
            "needs_video": True,
            "video_params": {"duration": 15, "voice": "female_active", "with_model": is_fashion},
        })
        return {
            "product_summary": product_info[:50],
            "target_audience": "年轻消费者",
            "platform_plans": plans,
            "total_estimated_credits": 15,
        }


# ══════════════════════════════════════════════════════════════
#  素材管理
# ══════════════════════════════════════════════════════════════

@router.post("/assets/upload")
async def upload_asset(
    file: UploadFile = File(...),
    category: str = Form("product"),
    product_id: str = Form(None),
    name: str = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传素材文件到素材库。"""
    # Validate file type
    content_type = file.content_type or ""
    if not (content_type.startswith("image/") or content_type.startswith("video/")):
        raise HTTPException(status_code=400, detail="仅支持图片和视频文件")

    file_type = "image" if content_type.startswith("image/") else "video"

    # Save file
    ext = os.path.splitext(file.filename or "file")[1] or ".jpg"
    filename = f"{uuid_mod.uuid4().hex[:12]}{ext}"
    save_dir = os.path.join(ASSETS_DIR, user.id[:8], category)
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, filename)

    content_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    asset = Asset(
        user_id=user.id,
        name=name or file.filename or filename,
        file_type=file_type,
        file_path=file_path,
        file_url=f"/static/assets/{user.id[:8]}/{category}/{filename}",
        file_size=len(content_bytes),
        category=category,
        product_id=product_id if product_id else None,
        extra_data={},
    )
    db.add(asset)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": asset.id,
            "name": asset.name,
            "file_type": asset.file_type,
            "file_url": asset.file_url,
            "file_size": asset.file_size,
            "category": asset.category,
        },
        "message": "素材上传成功",
        "error": None,
    }


@router.get("/assets/list")
async def list_assets_api(
    category: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出用户素材库。"""
    query = select(Asset).where(Asset.user_id == user.id)
    if category:
        query = query.where(Asset.category == category)
    query = query.order_by(Asset.created_at.desc()).limit(100)

    result = await db.execute(query)
    assets = result.scalars().all()

    return {
        "success": True,
        "data": {
            "assets": [
                {
                    "id": a.id,
                    "name": a.name,
                    "file_type": a.file_type,
                    "file_url": a.file_url,
                    "file_size": a.file_size,
                    "category": a.category,
                    "product_id": a.product_id,
                    "metadata": a.extra_data,
                    "ref_count": a.ref_count,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in assets
            ]
        },
        "message": "ok",
        "error": None,
    }


@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除素材。"""
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.user_id == user.id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")

    # Delete file
    if asset.file_path and os.path.exists(asset.file_path):
        os.remove(asset.file_path)

    await db.delete(asset)
    await db.flush()

    return {"success": True, "data": None, "message": "素材已删除", "error": None}


# ══════════════════════════════════════════════════════════════
#  商品主图生成
# ══════════════════════════════════════════════════════════════

class MainImageRequest(BaseModel):
    product_info: str = ""  # 可选：有素材时可不填
    source_asset_ids: list[str] | None = None
    styles: list[str] = ["white_bg", "scene", "detail", "selling_point"]
    with_model: bool = False
    model_asset_id: str | None = None
    size: str = "800*800"
    scene_description: str | None = None
    mood_keywords: list[str] | None = None
    custom_prompts: list[dict] | None = None  # 用户编辑后的prompt列表


class PromptPreviewRequest(BaseModel):
    product_info: str = ""
    source_asset_ids: list[str] | None = None
    styles: list[str] = ["white_bg", "scene", "detail", "selling_point"]
    scene_description: str | None = None
    mood_keywords: list[str] | None = None


@router.post("/main-image/preview-prompts")
async def preview_main_image_prompts(
    req: PromptPreviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """预览AI生成的主图提示词，用户可编辑后再生成。"""
    import json as _json

    # Load source assets
    vision_context = ""
    product_desc = req.product_info
    if req.source_asset_ids:
        for asset_id in req.source_asset_ids:
            asset = await db.get(Asset, asset_id)
            if asset:
                va = (asset.extra_data or {}).get("vision_analysis", "")
                if va:
                    if isinstance(va, dict):
                        vision_context += f"\n素材分析: {_json.dumps(va, ensure_ascii=False)}"
                        # 自动提取商品信息
                        if not product_desc:
                            product_desc = va.get("detected_category", asset.name)
                    else:
                        vision_context += f"\n素材分析: {va}"
                        if not product_desc:
                            product_desc = asset.name

    if not product_desc:
        product_desc = "商品"

    scene_desc = req.scene_description or product_desc
    mood = "、".join(req.mood_keywords) if req.mood_keywords else "专业、高端"

    architect_prompt = (
        f"你是一位电商视觉场景构建专家。请为以下商品生成主图的生图prompt。\n\n"
        f"商品信息：{product_desc}\n"
        f"场景描述：{scene_desc}\n"
        f"情绪关键词：{mood}\n"
        f"{vision_context}\n\n"
        f"需要生成的风格：{', '.join(req.styles)}\n\n"
        f"请输出JSON格式，包含 main_image_prompts 数组，每个元素包含：\n"
        f"- style: 风格key（如 white_bg, scene, detail, selling_point, model）\n"
        f"- prompt: 中文生图描述（详细、具体、适合通义万相，包含：主体描述→环境场景→光照→技术参数→风格美学）\n"
        f"- negative_prompt: 不要出现的元素\n\n"
        f"只输出JSON，不要其他内容。"
    )

    try:
        result = await ai_analyze_full(architect_prompt, task_type="scene_architect")
        raw_text = result.get("text", "")
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
        prompt_data = _json.loads(cleaned)
        prompts = prompt_data.get("main_image_prompts", [])
    except Exception as e:
        logger.warning(f"Preview prompt generation failed: {e}")
        # 降级：返回基础模板
        prompts = [
            {"style": s, "prompt": f"电商主图，{product_desc}，{s}风格，高清商业摄影", "negative_prompt": "文字、水印、模糊"}
            for s in req.styles
        ]

    return {
        "success": True,
        "data": {
            "prompts": prompts,
            "product_info_detected": product_desc,
            "cost": result.get("cost", 0) if "result" in dir() else 0,
        },
        "message": "提示词预览已生成",
        "error": None,
    }


@router.post("/main-image/generate")
async def generate_main_images(
    req: MainImageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成商品主图（5张套图）。产品图保真：抠图+换背景，不重新画产品。"""
    import json as _json
    from app.services.media.product_image import generate_product_main_images

    # Load source asset file paths from DB
    source_image_path = None
    if req.source_asset_ids:
        for asset_id in req.source_asset_ids:
            asset = await db.get(Asset, asset_id)
            if asset and asset.file_path and os.path.isfile(asset.file_path):
                source_image_path = asset.file_path
                break  # 取第一张有效素材

    if not source_image_path:
        return {
            "success": False, "data": None,
            "message": "请先上传商品素材图片", "error": "no_source_image",
        }

    # Build prompt_package from custom_prompts if provided
    prompt_package = None
    if req.custom_prompts:
        prompt_package = {"main_image_prompts": req.custom_prompts}

    # Use new product-fidelity pipeline
    results = await generate_product_main_images(
        source_image_path=source_image_path,
        styles=req.styles,
        product_info=req.product_info or "商品",
        prompt_package=prompt_package,
        size=800,
    )

    # Save generated images as assets
    saved = []
    for r in results:
        if not r.get("images"):
            continue
        for img in r["images"]:
            asset = Asset(
                user_id=user.id,
                name=f"主图_{r['style']}",
                file_type="image",
                file_path=img.get("local_path", ""),
                file_url=img.get("url", ""),
                file_size=0,
                category="generated_main",
                extra_data={"style": r["style"], "product_info": (req.product_info or "")[:100]},
            )
            db.add(asset)
            await db.flush()
            saved.append({
                "id": asset.id,
                "style": r["style"],
                "url": img.get("url", ""),
                "local_path": img.get("local_path", ""),
            })

    return {
        "success": True,
        "data": {
            "images": saved,
            "total_cost": sum(r.get("cost", 0) for r in results),
        },
        "message": f"已生成 {len(saved)} 张主图",
        "error": None,
    }


# ══════════════════════════════════════════════════════════════
#  AI模特
# ══════════════════════════════════════════════════════════════

class AIModelRequest(BaseModel):
    product_image_asset_id: str | None = None
    gender: str = "female"
    age_range: str = "20-25"
    style_tags: list[str] = []


@router.post("/ai-model/generate")
async def generate_ai_model(
    req: AIModelRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成AI虚拟模特。"""
    from app.services.media.virtual_model_gen import generate_virtual_model

    result = await generate_virtual_model(
        gender=req.gender,
        age_range=req.age_range,
        style_tags=req.style_tags,
    )

    if not result:
        return {"success": False, "data": None, "message": "模特生成失败", "error": "generation_failed"}

    # Auto-save to asset library
    asset = Asset(
        user_id=user.id,
        name=f"AI模特_{req.gender}_{req.age_range}",
        file_type="image",
        file_path=result.get("local_path", ""),
        file_url=result.get("url", ""),
        file_size=0,
        category="ai_model",
        extra_data={
            "gender": req.gender,
            "age_range": req.age_range,
            "style_tags": req.style_tags,
        },
    )
    db.add(asset)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": asset.id,
            "url": result.get("url", ""),
            "gender": req.gender,
            "age_range": req.age_range,
            "style_tags": req.style_tags,
        },
        "message": "AI模特已生成并保存",
        "error": None,
    }


@router.get("/ai-models")
async def list_ai_models(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出用户的AI模特。"""
    result = await db.execute(
        select(Asset)
        .where(Asset.user_id == user.id, Asset.category == "ai_model")
        .order_by(Asset.created_at.desc())
    )
    models = result.scalars().all()

    return {
        "success": True,
        "data": {
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "url": m.file_url,
                    "gender": m.extra_data.get("gender", ""),
                    "age_range": m.extra_data.get("age_range", ""),
                    "style_tags": m.extra_data.get("style_tags", []),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in models
            ]
        },
        "message": "ok",
        "error": None,
    }


# ══════════════════════════════════════════════════════════════
#  商品宣传视频
# ══════════════════════════════════════════════════════════════

class PromoVideoRequest(BaseModel):
    product_info: str
    image_asset_ids: list[str] = []
    model_asset_id: str | None = None
    duration: int = 15
    voice: str | None = None


@router.post("/promo-video/generate")
async def generate_promo_video_api(
    req: PromoVideoRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成商品宣传视频。"""
    from app.services.media.promo_video_gen import generate_promo_video

    # Resolve asset paths
    image_paths = []
    if req.image_asset_ids:
        result = await db.execute(
            select(Asset).where(
                Asset.id.in_(req.image_asset_ids),
                Asset.user_id == user.id,
            )
        )
        assets = result.scalars().all()
        image_paths = [a.file_path for a in assets if a.file_path]

    result = await generate_promo_video(
        product_info=req.product_info,
        product_images=image_paths,
        model_asset_id=req.model_asset_id,
        duration=req.duration,
        voice=req.voice,
    )

    if not result:
        return {"success": False, "data": None, "message": "视频生成失败", "error": "generation_failed"}

    # Save video as asset
    asset = Asset(
        user_id=user.id,
        name=f"宣传视频_{req.duration}s",
        file_type="video",
        file_path=result.get("video_path", ""),
        file_url=result.get("video_url", ""),
        file_size=0,
        category="generated_video",
        extra_data={"duration": req.duration, "product_info": req.product_info[:100]},
    )
    db.add(asset)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": asset.id,
            "video_url": result.get("video_url", ""),
            "video_path": result.get("video_path", ""),
            "duration": req.duration,
            "cost": result.get("cost", 0),
        },
        "message": "宣传视频已生成",
        "error": None,
    }


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
