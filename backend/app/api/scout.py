from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class MarketInsightRequest(BaseModel):
    keyword: str
    platform: str = "all"


@router.post("/market-insight")
def market_insight(req: MarketInsightRequest):
    # TODO: integrate Claude API for real analysis
    return {
        "success": True,
        "data": {
            "keyword": req.keyword,
            "market_size": 128500,
            "competition_score": 62,
            "avg_price": 89.5,
            "monthly_sales": 89200,
            "segments": [
                {"name": "高腰提臀款", "score": 92, "competition": "低"},
                {"name": "男士运动款", "score": 85, "competition": "中"},
            ],
        },
        "message": "分析完成",
        "error": None,
    }


@router.post("/recommendation")
def recommendation():
    return {
        "success": True,
        "data": {
            "products": [
                {"name": "高腰提臀瑜伽裤", "score": 92, "metrics": {"demand": 88, "profit": 90, "competition": 85}},
            ]
        },
        "message": "推荐完成",
        "error": None,
    }


@router.get("/competitors")
def get_competitors():
    return {"success": True, "data": {"competitors": []}, "message": "ok", "error": None}


@router.post("/profit-calc")
def profit_calc(cost: float = 22, price: float = 89, commission_rate: float = 0.03):
    profit = price - cost - price * commission_rate
    margin = profit / price * 100
    return {
        "success": True,
        "data": {"net_profit": round(profit, 2), "margin": round(margin, 1)},
        "message": "ok",
        "error": None,
    }
