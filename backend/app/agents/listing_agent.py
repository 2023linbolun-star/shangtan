"""
Listing Agent — 标题优化 + SEO + 违规检测。
"""

from app.agents.base import BaseAgent, AgentContext
from app.agents.prompts import build_agent_system_prompt
from app.agents.memory import MemoryStore
from app.services.prompts.listing import build_title_prompt
from app.services.violation_checker import check_violations

ROLE = """你是商探AI的Listing优化首席——一位多平台SEO专家。

你同时管理过200+店铺在淘宝/抖音/拼多多/小红书/京东的Listing优化。
你优化过的标题平均提升搜索曝光30%。
你最擅长的是"在有限字符内塞入最大搜索价值"——标题的每一个字都是经过精算的。

【各平台标题规则】
- 淘宝(60字符)：品类核心词+属性+功能+场景+长尾，不堆砌
- 抖音(60字符)：品类词+核心卖点+人群场景，简洁有吸引力
- 拼多多(60字符)：品类词+属性堆叠+信任词(包邮/正品)
- 小红书(30字符)：种草感标题，含emoji

【绝对禁止】
- 禁止生成超出字符限制的标题
- 禁止在非旗舰店拼多多标题放品牌名
- 禁止遗漏违规检测
- 禁止用同一标题全平台"""


class ListingAgent(BaseAgent):
    agent_type = "listing"

    async def observe(self, ctx: AgentContext) -> dict:
        store = MemoryStore(self.db)
        return {
            "user_dna": await store.get_user_dna(ctx.user_id),
            "few_shots": await store.get_few_shots(ctx.user_id, self.agent_type),
            "guardrails": await store.get_failure_guardrails(ctx.user_id, self.agent_type),
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        platforms = ctx.task_input.get("platforms", [])
        return {"reasoning": f"为 {len(platforms)} 个平台优化标题"}

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        keyword = ctx.task_input.get("keyword", "")
        platforms = ctx.task_input.get("platforms", ["taobao", "douyin"])

        system = build_agent_system_prompt(
            ROLE,
            observation.get("user_dna"),
            observation.get("few_shots"),
            observation.get("guardrails"),
        )

        prompt = build_title_prompt(
            product_name=keyword,
            category=ctx.task_input.get("category", ""),
            platforms=platforms,
        )

        result = await self._ai_call(prompt, task_type="listing", system=system)

        # 对每个生成的标题做违规检测
        import json
        try:
            parsed = json.loads(result["text"])
            listings = parsed.get("listings", [])
            for listing in listings:
                title = listing.get("optimized_title", "")
                platform = listing.get("platform", "")
                v = check_violations(title, platform=platform)
                listing["violation_check"] = v

                # 红色违规自动修复
                if v["risk_level"] == "red":
                    for issue in v["issues"]:
                        word = issue.get("keyword", "")
                        if word and word in title:
                            title = title.replace(word, "")
                    listing["optimized_title"] = title.strip()
                    listing["violation_check"] = check_violations(title, platform=platform)
                    listing["auto_fixed"] = True
        except (json.JSONDecodeError, KeyError):
            listings = []

        return {
            "listings": listings,
            "raw_response": result["text"],
            "model": result["model"],
            "cost": result["cost"],
        }
