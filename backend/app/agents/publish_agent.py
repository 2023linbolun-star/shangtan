"""
Publish Agent — 发布排期专家。
"""

from app.agents.base import BaseAgent, AgentContext
from app.agents.prompts import build_agent_system_prompt
from app.agents.memory import MemoryStore

ROLE = """你是商探AI的发布排期首席——管理过50+品牌多平台发布节奏的运营经理。

【各平台最佳发布时间】
- 抖音：工作日 21:00-22:00 最佳，周末 15:00-17:00
- 小红书：12:00-14:00 或 20:00-22:00，种草笔记比商品上架提前7-14天
- 淘宝：新品有7-14天权重加成，大促前30天上架最佳
- 拼多多：上架后立即参加新品推荐，流量高峰 20:00-22:00

【冷启动顺序】
1. 小红书种草（提前14天）→ 建立口碑
2. 抖音短视频（提前7天）→ 制造曝光
3. 淘宝/天猫上架（正式发售日）→ 承接搜索
4. 拼多多上架（发售日+3天）→ 价格敏感用户

【绝对禁止】
- 禁止所有平台同一天发布
- 禁止忽略大促日历
- 禁止给出没有具体时间的模糊建议"""


class PublishAgent(BaseAgent):
    agent_type = "publish"

    async def observe(self, ctx: AgentContext) -> dict:
        store = MemoryStore(self.db)
        return {
            "user_dna": await store.get_user_dna(ctx.user_id),
            "guardrails": await store.get_failure_guardrails(ctx.user_id, self.agent_type),
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        return {"reasoning": "生成发布排期建议"}

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        keyword = ctx.task_input.get("keyword", "")
        platforms = ctx.task_input.get("platforms", [])

        system = build_agent_system_prompt(
            ROLE,
            observation.get("user_dna"),
            failure_guardrails=observation.get("guardrails"),
        )

        from datetime import date
        today = date.today().isoformat()

        prompt = f"""请为以下产品生成发布排期建议。

关键词：{keyword}
目标平台：{', '.join(platforms)}
当前日期：{today}

输出JSON:
{{
  "recommended_order": ["先发平台", "后发平台"],
  "platform_schedule": [
    {{
      "platform": "平台名",
      "publish_date": "建议日期",
      "best_time": "最佳时间段",
      "reason": "原因",
      "checklist": ["准备事项1", "准备事项2"]
    }}
  ],
  "calendar_alerts": ["近期大促提醒"],
  "cold_start_tips": "冷启动策略建议"
}}

只输出JSON。"""

        result = await self._ai_call(prompt, task_type="batch", system=system)

        return {
            "publish_schedule": result["text"],
            "model": result["model"],
            "cost": result["cost"],
        }
