from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


@router.get("/products")
def list_products():
    return {"success": True, "data": {"products": []}, "message": "ok", "error": None}


@router.post("/optimize")
def optimize_listing(product_id: str, platform: str = "douyin"):
    # TODO: Claude API
    return {
        "success": True,
        "data": {
            "original_title": "高腰瑜伽裤女",
            "optimized_title": "高腰提臀瑜伽裤女 冰丝速干运动健身裤 夏季薄款弹力紧身裤",
            "score": 85,
            "bullet_points": ["高腰收腹设计", "蜜桃提臀剪裁", "冰丝面料透气速干"],
        },
        "message": "优化完成",
        "error": None,
    }


@router.post("/check-violation")
def check_violation(product_id: str):
    return {
        "success": True,
        "data": {
            "risk_level": "yellow",
            "issues": [{"type": "平台规则", "detail": "标题包含「最」字", "suggestion": "删除或替换"}],
        },
        "message": "检测完成",
        "error": None,
    }


@router.post("/keywords/expand")
def expand_keywords(keyword: str):
    return {"success": True, "data": {"groups": {}}, "message": "ok", "error": None}


@router.post("/export")
def export_listing(product_id: str, platform: str):
    return {"success": True, "data": {"download_url": "/mock/export.csv"}, "message": "导出完成", "error": None}
