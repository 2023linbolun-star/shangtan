"""
PerformanceAgent — 数据分析专家。
分析商品表现，做出加量/维持/淘汰决策。
"""
from app.agents.base import BaseAgent, AgentContext
import logging

logger = logging.getLogger("shangtanai.agent.performance")

ROLE = """你是商探AI的数据分析师——根据真实销售数据判断每个商品的去留。

【决策标准（上架7天后）】

淘汰条件（任一满足）：
- 7天0订单
- 退货率 > 40% 且 ≥ 10单
- 单品净利润为负
- 客户投诉 > 3次

维持条件：
- 1-10订单
- 正利润
- 退货率 20-40%

加量条件（全部满足）：
- > 10订单
- 净利润 > 10元/件
- 退货率 < 20%
- 内容互动率高于平均

【加量策略（仅在自然验证通过后）】
- ≥ 5个自然订单
- 净利率 ≥ 25%
- 退货率 < 30%
满足以上条件才考虑付费广告"""


class PerformanceAgent(BaseAgent):
    agent_type = "performance_review"

    async def observe(self, ctx: AgentContext) -> dict:
        """Collect product performance data."""
        product_data = ctx.task_input.get("product_data", {})
        return {
            "product_id": ctx.task_input.get("product_id"),
            "product_name": product_data.get("name", "未知"),
            "days_listed": product_data.get("days_listed", 0),
            "total_orders": product_data.get("total_orders", 0),
            "total_revenue": product_data.get("total_revenue", 0),
            "total_cost": product_data.get("total_cost", 0),
            "return_rate": product_data.get("return_rate", 0),
            "complaints": product_data.get("complaints", 0),
            "content_metrics": product_data.get("content_metrics", {}),
            "organic_orders": product_data.get("organic_orders", 0),
            "net_margin": product_data.get("net_margin", 0),
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        orders = observation["total_orders"]
        days = observation["days_listed"]
        return_rate = observation["return_rate"]
        net_margin = observation["net_margin"]
        complaints = observation["complaints"]

        # Deterministic pre-decision
        if days < 7:
            decision = "too_early"
            reasoning = f"上架仅 {days} 天，数据不足"
        elif orders == 0:
            decision = "kill"
            reasoning = "7天0订单"
        elif return_rate > 0.40 and orders >= 10:
            decision = "kill"
            reasoning = f"退货率过高: {return_rate:.0%}"
        elif complaints > 3:
            decision = "kill"
            reasoning = f"投诉过多: {complaints}次"
        elif net_margin < 0:
            decision = "kill"
            reasoning = "净利润为负"
        elif orders > 10 and net_margin > 0.10 and return_rate < 0.20:
            decision = "scale"
            reasoning = f"{orders}订单, 利润率{net_margin:.0%}, 退货率{return_rate:.0%}"
        else:
            decision = "maintain"
            reasoning = f"{orders}订单, 表现一般"

        return {
            "reasoning": reasoning,
            "pre_decision": decision,
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        pre_decision = plan.get("pre_decision", "maintain")

        if pre_decision == "too_early":
            return {
                "decision": "too_early",
                "reasoning": plan["reasoning"],
                "recommendation": "继续观察",
                "ad_eligible": False,
            }

        # Use AI for detailed analysis and recommendations
        prompt = f"""分析以下商品表现数据，给出详细建议。

## 商品：{observation['product_name']}
- 上架天数：{observation['days_listed']}
- 总订单：{observation['total_orders']}
- 总营收：\u00a5{observation['total_revenue']}
- 退货率：{observation['return_rate']:.1%}
- 净利率：{observation['net_margin']:.1%}
- 自然订单：{observation['organic_orders']}
- 投诉数：{observation['complaints']}

## 系统预判：{pre_decision.upper()} — {plan['reasoning']}

请输出JSON：
{{
  "decision": "scale/maintain/kill",
  "confidence": 0.0-1.0,
  "reasoning": "详细分析",
  "action_items": ["具体行动建议"],
  "ad_eligible": true/false,
  "suggested_ad_budget": 0 或 建议日预算（仅scale且满足广告条件时）,
  "risk_factors": ["风险点"]
}}"""

        result = await self._ai_call(prompt, task_type="analysis")

        return {
            "pre_decision": pre_decision,
            "ai_analysis": result["text"],
            "ai_cost": result.get("cost", 0),
            "product_id": observation["product_id"],
            "product_name": observation["product_name"],
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        pre = output.get("pre_decision", "")
        has_analysis = "decision" in output.get("ai_analysis", "")
        confidence = 0.85 if pre in ("kill", "scale") else 0.6
        return {"confidence": confidence, "issues": [] if has_analysis else ["AI分析未返回有效结果"]}
