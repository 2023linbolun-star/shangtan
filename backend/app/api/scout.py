"""
选品雷达 API — 基于联盟 API 真实数据 + AI 分析

数据流：
  用户输入关键词
  → 多平台联盟 API 并发搜索（淘宝联盟 + 多多进宝 + 抖音精选联盟）
  → 小红书开放平台（种草热度）
  → 数据聚合统计
  → AI 基于真实数据做综合分析（竞争格局、进入难度、细分机会）
  → 输出选品报告

核心原则：AI 只做分析决策，不编造数据。所有数据来自联盟 API。
"""

import json
import re
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai_engine import ai_analyze
from app.services.scout_aggregator import ScoutAggregator

router = APIRouter()
aggregator = ScoutAggregator()


# --- Request/Response Models ---


class MarketInsightRequest(BaseModel):
    keyword: str
    platforms: Optional[list[str]] = None  # 不指定则查询全部已配置平台
    page: int = 1
    page_size: int = 20
    sort: str = "default"  # default / sales / price_asc / price_desc / commission


class ProfitCalcRequest(BaseModel):
    cost: float = 0  # 采购成本
    price: float = 0  # 售价
    commission_rate: float = 0.03  # 平台佣金率
    logistics: float = 0  # 物流成本
    packaging: float = 0  # 包装成本
    ad_cost: float = 0  # 单件广告费
    return_rate: float = 0.05  # 退货率


# --- AI Prompt ---


MARKET_ANALYSIS_PROMPT = """你是一位专业的电商市场分析师。请基于以下**真实的联盟 API 数据**，生成市场分析报告。

重要：以下所有数据均来自各平台联盟 API 的真实返回，请基于这些真实数据进行分析，不要编造新的数据。

{data_context}

---

请严格按照以下 JSON 格式返回分析结果，不要包含任何其他文字，只返回 JSON：

{{
  "competition_score": <基于真实数据评估的竞争难度 0-100，整数>,
  "entry_difficulty": "<低/中/高>",
  "entry_difficulty_reason": "<为什么给出这个难度评级，基于数据说明>",
  "market_analysis": "<200字以内的市场整体分析，引用真实数据>",
  "competition_breakdown": [
    {{"name": "头部卖家(月销>1000)", "value": <估算百分比>}},
    {{"name": "中部卖家(月销100-1000)", "value": <估算百分比>}},
    {{"name": "长尾卖家(月销<100)", "value": <估算百分比>}}
  ],
  "segments": [
    {{
      "name": "<从商品标题中提取的细分方向>",
      "score": <推荐评分 0-100>,
      "competition": "低/中/高",
      "trend": "↑/→/↓",
      "reason": "<推荐原因>",
      "tags": ["标签1", "标签2"]
    }}
  ],
  "suggestions": [
    "<基于数据的具体建议1>",
    "<基于数据的具体建议2>",
    "<基于数据的具体建议3>"
  ]
}}

请确保：
1. 竞争难度评分基于实际的商品数量、价格分布、销量分布
2. 细分方向从实际商品标题中提取关键词归纳
3. 所有分析结论都有数据支撑"""


def _parse_ai_response(raw: str) -> dict:
    """Extract JSON from AI response, handling markdown code blocks."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")
    return json.loads(cleaned)


# --- Endpoints ---


@router.post("/market-insight")
async def market_insight(req: MarketInsightRequest):
    """市场洞察：多平台真实数据 + AI 分析。"""
    try:
        # Step 1: 多平台并发搜索，获取真实数据
        agg_data = await aggregator.search(
            keyword=req.keyword,
            platforms=req.platforms,
            page=req.page,
            page_size=req.page_size,
            sort=req.sort,
        )

        # Step 2: 构建数据摘要
        price_summary = agg_data.price_summary()
        sales_summary = agg_data.sales_summary()
        commission_summary = agg_data.commission_summary()
        price_bands = agg_data.price_bands()
        platform_breakdown = agg_data.platform_breakdown()
        top_products = agg_data.top_products(limit=10)

        # Step 3: AI 基于真实数据做分析
        ai_analysis = None
        if agg_data.total_products > 0:
            context = agg_data.to_ai_context()
            prompt = MARKET_ANALYSIS_PROMPT.format(data_context=context)
            raw = await ai_analyze(prompt, task_type="analysis")
            try:
                ai_analysis = _parse_ai_response(raw)
            except (json.JSONDecodeError, KeyError):
                ai_analysis = None

        # Step 4: 组装响应
        response_data = {
            "keyword": req.keyword,
            # 真实数据统计
            "data_sources": {
                "configured": agg_data.configured_platforms,
                "unconfigured": agg_data.unconfigured_platforms,
                "errors": agg_data.errors,
            },
            "total_products": agg_data.total_products,
            "price": price_summary,
            "sales": sales_summary,
            "commission": commission_summary,
            "price_bands": price_bands,
            "platform_breakdown": platform_breakdown,
            "top_products": top_products,
            # 小红书种草热度
            "xhs_buzz": {
                "note_count": agg_data.xhs_data.note_count,
                "avg_likes": agg_data.xhs_data.avg_likes,
                "avg_collects": agg_data.xhs_data.avg_collects,
                "buzz_score": agg_data.xhs_data.buzz_score,
                "hot_notes": agg_data.xhs_data.hot_notes,
            }
            if agg_data.xhs_data
            else None,
            # AI 分析结果
            "ai_analysis": ai_analysis,
        }

        return {
            "success": True,
            "data": response_data,
            "message": f"分析完成，数据来自 {', '.join(agg_data.configured_platforms) or '无已配置平台'}",
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "message": "分析失败，请稍后重试",
            "error": str(e),
        }


@router.get("/platforms/status")
async def platform_status():
    """查询各平台 API 配置状态。"""
    adapters = {
        "taobao": aggregator.taobao,
        "pinduoduo": aggregator.pinduoduo,
        "douyin": aggregator.douyin,
        "xiaohongshu": aggregator.xiaohongshu,
    }
    status = {}
    for name, adapter in adapters.items():
        status[name] = {
            "configured": adapter.is_configured(),
            "name": {
                "taobao": "淘宝联盟",
                "pinduoduo": "多多进宝",
                "douyin": "抖音精选联盟（聚推客）",
                "xiaohongshu": "小红书开放平台",
            }[name],
        }
    return {"success": True, "data": status, "message": "ok", "error": None}


@router.post("/recommendation")
async def recommendation(keyword: str = "", platforms: Optional[list[str]] = None):
    """选品推荐：基于真实数据的商品推荐列表。"""
    if not keyword:
        return {
            "success": True,
            "data": {"products": []},
            "message": "请输入关键词",
            "error": None,
        }

    agg_data = await aggregator.search(keyword=keyword, platforms=platforms)
    top = agg_data.top_products(limit=20)

    return {
        "success": True,
        "data": {
            "products": top,
            "total": agg_data.total_products,
            "data_sources": agg_data.configured_platforms,
        },
        "message": "推荐完成",
        "error": None,
    }


@router.get("/competitors")
def get_competitors():
    return {
        "success": True,
        "data": {"competitors": []},
        "message": "ok",
        "error": None,
    }


@router.post("/profit-calc")
def profit_calc(req: ProfitCalcRequest):
    """利润计算器：支持完整成本结构。"""
    effective_price = req.price * (1 - req.return_rate)
    total_cost = (
        req.cost
        + req.logistics
        + req.packaging
        + req.ad_cost
        + req.price * req.commission_rate
    )
    net_profit = effective_price - total_cost
    margin = (net_profit / req.price * 100) if req.price > 0 else 0

    # 盈亏平衡售价
    fixed_cost = req.cost + req.logistics + req.packaging + req.ad_cost
    breakeven_price = fixed_cost / (1 - req.return_rate - req.commission_rate) if (1 - req.return_rate - req.commission_rate) > 0 else 0

    # 不同售价的利润对比
    price_comparison = []
    for multiplier in [0.8, 0.9, 1.0, 1.1, 1.2, 1.5]:
        test_price = round(req.price * multiplier, 2)
        eff = test_price * (1 - req.return_rate)
        tc = req.cost + req.logistics + req.packaging + req.ad_cost + test_price * req.commission_rate
        np_ = eff - tc
        price_comparison.append({
            "price": test_price,
            "net_profit": round(np_, 2),
            "margin": round(np_ / test_price * 100, 1) if test_price > 0 else 0,
        })

    return {
        "success": True,
        "data": {
            "net_profit": round(net_profit, 2),
            "margin": round(margin, 1),
            "breakeven_price": round(breakeven_price, 2),
            "total_cost": round(total_cost, 2),
            "effective_revenue": round(effective_price, 2),
            "cost_breakdown": {
                "product_cost": req.cost,
                "logistics": req.logistics,
                "packaging": req.packaging,
                "ad_cost": req.ad_cost,
                "commission": round(req.price * req.commission_rate, 2),
                "return_loss": round(req.price * req.return_rate, 2),
            },
            "price_comparison": price_comparison,
        },
        "message": "ok",
        "error": None,
    }
