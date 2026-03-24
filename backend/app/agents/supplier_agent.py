"""
SupplierAgent — 供应商匹配专家。
在1688搜索最优一件代发供应商。
"""
from app.agents.base import BaseAgent, AgentContext
import httpx
import logging

logger = logging.getLogger("shangtanai.agent.supplier")

ROLE = """你是商探AI的供应链专家——专门在1688上找到最优的一件代发供应商。

【核心原则】
- 只推荐支持一件代发的供应商
- 价格不是唯一标准，发货速度、退货政策、店铺评分同样重要
- 必须计算完整成本：采购价 + 运费(3-8元) + 包装(1-3元)
- 新供应商首单建议小批量测试

【评估维度】
- 价格竞争力 30%
- 一件代发支持 25%（必须项）
- 供应商评级 20%
- 发货速度 15%
- 退货政策 10%"""


class SupplierAgent(BaseAgent):
    agent_type = "supplier_match"

    async def observe(self, ctx: AgentContext) -> dict:
        """Search 1688 for suppliers."""
        keyword = ctx.task_input.get("keyword", "")
        search_keyword = ctx.task_input.get("supplier_search_keyword", keyword)

        # Try 1688 API if configured
        from app.core.config import ALIBABA_APP_KEY
        suppliers = []
        errors = {}

        if ALIBABA_APP_KEY:
            try:
                suppliers = await self._search_1688_api(search_keyword)
            except Exception as e:
                errors["1688_api"] = str(e)
                logger.warning("1688 API failed: %s, using fallback", e)

        # If no API results, generate mock data for development
        if not suppliers:
            logger.info("No 1688 API data, using AI estimation for %s", keyword)

        return {
            "keyword": keyword,
            "search_keyword": search_keyword,
            "suppliers": suppliers,
            "supplier_count": len(suppliers),
            "errors": errors,
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        count = observation["supplier_count"]
        return {
            "reasoning": f"找到 {count} 家供应商" if count > 0 else "未找到API供应商，将使用AI估算成本",
            "strategy": "rank_and_select" if count > 0 else "ai_estimate",
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        keyword = observation["keyword"]
        suppliers = observation["suppliers"]

        # Use AI to analyze suppliers or estimate if no API data
        if suppliers:
            supplier_text = "\n".join(
                f"- {s.get('title', 'N/A')} | 价格: \u00a5{s.get('price', 0)} | "
                f"月销: {s.get('monthly_sales', 'N/A')} | 评分: {s.get('rating', 'N/A')}"
                for s in suppliers[:20]
            )
            context = f"## 1688搜索结果 ({len(suppliers)} 家)\n{supplier_text}"
        else:
            context = f"## 无API数据，请根据品类 '{keyword}' 估算合理的采购成本范围"

        prompt = f"""分析以下供应商数据，推荐Top 3最优一件代发供应商。

## 目标商品关键词：{keyword}

{context}

请输出JSON格式：
{{
  "recommended_suppliers": [
    {{
      "rank": 1,
      "name": "供应商名称",
      "product_title": "商品标题",
      "unit_price": 采购单价（元）,
      "shipping_cost": 预估运费（元）,
      "packaging_cost": 预估包装费（元）,
      "total_landed_cost": 完整到手成本（元）,
      "rating": "供应商评分",
      "supports_dropship": true/false,
      "min_order_qty": 最小起订量,
      "shipping_days": 预估发货天数,
      "advantages": "优势",
      "risks": "风险点"
    }}
  ],
  "cost_summary": {{
    "avg_cost": 平均采购成本,
    "min_cost": 最低成本,
    "max_cost": 最高成本,
    "recommended_retail_price_range": "建议零售价范围"
  }},
  "supply_assessment": "供应链评估总结"
}}"""

        result = await self._ai_call(prompt, task_type="analysis")

        return {
            "ai_analysis": result["text"],
            "ai_cost": result.get("cost", 0),
            "keyword": keyword,
            "supplier_count": observation["supplier_count"],
            "has_api_data": observation["supplier_count"] > 0,
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        analysis = output.get("ai_analysis", "")
        has_suppliers = "recommended_suppliers" in analysis
        has_api = output.get("has_api_data", False)

        confidence = 0.8 if (has_suppliers and has_api) else 0.5 if has_suppliers else 0.3
        issues = []
        if not has_suppliers:
            issues.append("未找到供应商推荐")
        if not has_api:
            issues.append("1688 API未返回数据，使用AI估算")

        return {"confidence": confidence, "issues": issues}

    async def _search_1688_api(self, keyword: str) -> list[dict]:
        """Search 1688 Open Platform API."""
        from app.core.config import ALIBABA_APP_KEY, ALIBABA_APP_SECRET
        if not ALIBABA_APP_KEY:
            return []

        # TODO: Implement actual 1688 API call with OAuth signature
        # For now return empty - will be implemented when API credentials are ready
        logger.info("1688 API search for: %s (credentials: %s)", keyword, "configured" if ALIBABA_APP_KEY else "missing")
        return []
