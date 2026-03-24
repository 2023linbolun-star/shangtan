"""上架中心 API — 真实 AI Listing 优化"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User, Product
from app.middleware.auth import get_current_user
from app.services.ai_engine import ai_analyze_full
from app.services.prompts.listing import build_title_prompt, build_keyword_expand_prompt
from app.services.violation_checker import check_violations

router = APIRouter()


class OptimizeRequest(BaseModel):
    product_name: str
    category: str = ""
    platforms: list[str] = ["taobao", "douyin"]
    keywords: list[str] | None = None


class ViolationCheckRequest(BaseModel):
    text: str
    platform: str = ""
    category: str = ""


@router.get("/products")
async def list_products(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's products."""
    result = await db.execute(
        select(Product)
        .where(Product.user_id == user.id)
        .order_by(Product.created_at.desc())
        .limit(50)
    )
    products = result.scalars().all()

    return {
        "success": True,
        "data": {
            "products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "keyword": p.keyword,
                    "platform": p.platform,
                    "price": p.price,
                    "cost": p.cost,
                    "status": p.status.value,
                    "risk_tags": p.risk_tags,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in products
            ]
        },
        "message": "ok",
        "error": None,
    }


@router.post("/optimize")
async def optimize_listing(
    req: OptimizeRequest,
    user: User = Depends(get_current_user),
):
    """AI-powered listing title optimization for multiple platforms."""
    prompt = build_title_prompt(
        product_name=req.product_name,
        category=req.category,
        platforms=req.platforms,
        keywords=req.keywords,
    )

    result = await ai_analyze_full(prompt, task_type="listing")

    # Run violation check on each generated title
    violation_results = {}
    try:
        import json
        parsed = json.loads(result["text"])
        listings = parsed.get("listings", [])
        for listing in listings:
            title = listing.get("optimized_title", "")
            platform = listing.get("platform", "")
            v = check_violations(title, platform=platform, category=req.category)
            listing["violation_check"] = v
    except (json.JSONDecodeError, KeyError):
        listings = []

    return {
        "success": True,
        "data": {
            "raw_response": result["text"],
            "listings": listings,
            "ai_model": result["model"],
            "cost_usd": round(result["cost"], 6),
        },
        "message": "优化完成",
        "error": None,
    }


@router.post("/check-violation")
async def check_violation(req: ViolationCheckRequest):
    """Check text for violations (ad law + platform rules)."""
    result = check_violations(
        text=req.text,
        platform=req.platform,
        category=req.category,
    )
    return {
        "success": True,
        "data": result,
        "message": "检测完成",
        "error": None,
    }


@router.post("/keywords/expand")
async def expand_keywords(keyword: str, user: User = Depends(get_current_user)):
    """AI-powered keyword expansion."""
    prompt = build_keyword_expand_prompt(keyword)
    result = await ai_analyze_full(prompt, task_type="keywords")

    return {
        "success": True,
        "data": {
            "raw_response": result["text"],
            "ai_model": result["model"],
            "cost_usd": round(result["cost"], 6),
        },
        "message": "拓展完成",
        "error": None,
    }


@router.post("/export")
async def export_listing(product_id: str, platform: str, user: User = Depends(get_current_user)):
    """Export listing — placeholder for CSV/Excel generation."""
    return {
        "success": True,
        "data": {"download_url": None, "message": "导出功能开发中"},
        "message": "ok",
        "error": None,
    }
