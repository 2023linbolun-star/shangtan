"""
AdAgent — 广告投放专家。
仅在自然流量验证通过后才启用，控制广告投放策略。
"""
from app.agents.base import BaseAgent, AgentContext
import logging

logger = logging.getLogger("shangtanai.agent.ad")

ROLE = """你是商探AI的广告投放专家。

【核心原则】
- 广告是加速器，不是起步方式。只有自然流量验证成功的品才投广告
- 启用条件：≥5个自然订单 + 净利率≥25% + 退货率<30%
- 从最低预算开始（100元/天），ROI达标才加量
- ROI低于1.5自动暂停，低于1.0立即关停

【平台广告工具】
- 千川（抖音）：短视频投流，适合内容型商品
- 直通车/万相台（淘宝）：搜索广告，适合搜索需求明确的商品
- 多多搜索（拼多多）：搜索广告，适合价格敏感型商品"""


class AdAgent(BaseAgent):
    agent_type = "ad_create"

    async def observe(self, ctx: AgentContext) -> dict:
        product_data = ctx.task_input.get("product_data", {})
        return {
            "product_id": ctx.task_input.get("product_id"),
            "product_name": product_data.get("name", ""),
            "platform": ctx.task_input.get("platform", ""),
            "organic_orders": product_data.get("organic_orders", 0),
            "net_margin": product_data.get("net_margin", 0),
            "return_rate": product_data.get("return_rate", 0),
            "budget_limit": ctx.task_input.get("budget_limit", 0),
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        # Check eligibility
        eligible = (
            observation["organic_orders"] >= 5
            and observation["net_margin"] >= 0.25
            and observation["return_rate"] < 0.30
        )

        if not eligible:
            reasons = []
            if observation["organic_orders"] < 5:
                reasons.append(f"自然订单不足: {observation['organic_orders']}/5")
            if observation["net_margin"] < 0.25:
                reasons.append(f"净利率不足: {observation['net_margin']:.0%}/25%")
            if observation["return_rate"] >= 0.30:
                reasons.append(f"退货率过高: {observation['return_rate']:.0%}/30%")
            return {
                "reasoning": f"不满足广告投放条件: {', '.join(reasons)}",
                "eligible": False,
            }

        return {
            "reasoning": "满足广告投放条件，准备生成投放方案",
            "eligible": True,
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        if not plan.get("eligible", False):
            return {
                "eligible": False,
                "reasoning": plan["reasoning"],
                "ad_plan": None,
            }

        observation = await self.observe(ctx)
        prompt = f"""为以下商品生成广告投放方案。

## 商品信息
- 商品：{observation['product_name']}
- 平台：{observation['platform']}
- 自然订单：{observation['organic_orders']}
- 净利率：{observation['net_margin']:.1%}
- 退货率：{observation['return_rate']:.1%}
- 预算上限：\u00a5{observation['budget_limit']}/天

请输出JSON：
{{
  "platform_tool": "千川/直通车/多多搜索",
  "daily_budget": 建议日预算（不超过上限）,
  "bid_strategy": "出价策略",
  "target_keywords": ["投放关键词"],
  "target_audience": "目标人群描述",
  "creative_suggestions": ["素材建议"],
  "expected_roas": 预期ROI,
  "stop_loss_roas": 止损ROI阈值,
  "optimization_cycle": "优化周期"
}}"""

        result = await self._ai_call(prompt, task_type="analysis")

        return {
            "eligible": True,
            "ai_analysis": result["text"],
            "ai_cost": result.get("cost", 0),
            "product_name": observation["product_name"],
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        if not output.get("eligible"):
            return {"confidence": 0.9, "issues": [output.get("reasoning", "")]}
        has_plan = "daily_budget" in output.get("ai_analysis", "")
        return {"confidence": 0.7 if has_plan else 0.4, "issues": []}
