"""
Content Agent — 内容生成调度器 + 平台 Sub-agents。
根据目标平台并行派发专属 Sub-agent 生成内容。
"""

import asyncio
from app.agents.base import BaseAgent, AgentContext
from app.agents.prompts import build_agent_system_prompt
from app.agents.memory import MemoryStore
from app.services.prompts import content_douyin, content_xiaohongshu, content_taobao, content_pdd
from app.services.violation_checker import check_violations


class ContentAgent(BaseAgent):
    """内容调度器：按平台派发 Sub-agent 并行生成。"""
    agent_type = "content"

    async def observe(self, ctx: AgentContext) -> dict:
        return {"platforms": ctx.task_input.get("platforms", [])}

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        platforms = observation["platforms"]
        return {
            "reasoning": f"需要为 {len(platforms)} 个平台生成内容，并行执行",
            "platforms": platforms,
        }

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        platforms = plan["platforms"]
        agents_and_contexts = []

        for platform in platforms:
            sub_ctx = AgentContext(
                user_id=ctx.user_id,
                pipeline_id=ctx.pipeline_id,
                task_input={**ctx.task_input, "platform": platform},
                user_dna=ctx.user_dna,
                few_shot_examples=ctx.few_shot_examples,
                failure_guardrails=ctx.failure_guardrails,
            )
            if platform in ("douyin", "kuaishou"):
                agents_and_contexts.append((DouyinContentAgent, sub_ctx))
            elif platform == "xiaohongshu":
                agents_and_contexts.append((XHSContentAgent, sub_ctx))
            elif platform in ("taobao", "tmall"):
                agents_and_contexts.append((TaobaoContentAgent, sub_ctx))
            elif platform == "pinduoduo":
                agents_and_contexts.append((PDDContentAgent, sub_ctx))

        # 并行执行所有平台 Sub-agent
        results = await self._spawn_parallel(agents_and_contexts)

        contents = []
        total_cost = 0
        for r in results:
            if r.success:
                contents.append(r.output)
                total_cost += sum(c.get("cost", 0) for c in r.ai_calls)

        return {
            "generated_contents": contents,
            "ai_cost": ctx.task_input.get("ai_cost", 0) + total_cost,
        }


# ── Platform Sub-agents ──

class _PlatformContentAgent(BaseAgent):
    """平台内容 Sub-agent 基类。"""
    prompt_module = None  # Override
    task_type = "content_social"

    async def observe(self, ctx: AgentContext) -> dict:
        store = MemoryStore(self.db)
        platform = ctx.task_input.get("platform", "")
        user_dna = await store.get_user_dna(ctx.user_id)
        few_shots = await store.get_few_shots(ctx.user_id, self.agent_type)
        guardrails = await store.get_failure_guardrails(ctx.user_id, self.agent_type)
        return {
            "platform": platform,
            "user_dna": user_dna,
            "few_shots": few_shots,
            "guardrails": guardrails,
        }

    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        return {"reasoning": f"为 {observation['platform']} 生成内容"}

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        platform = observation["platform"]

        # 构建产品信息
        product_info = self._build_product_info(ctx)

        # 构建 prompt
        prompt = self.prompt_module.build_prompt(
            product_info=product_info,
            style=ctx.task_input.get("config", {}).get("style", "种草"),
            notes=ctx.task_input.get("config", {}).get("notes", ""),
        )

        system = build_agent_system_prompt(
            self.prompt_module.SYSTEM,
            observation.get("user_dna"),
            observation.get("few_shots"),
            observation.get("guardrails"),
        )

        result = await self._ai_call(prompt, task_type=self.task_type, system=system)

        # 违规检测 + 自动修复
        violation = check_violations(result["text"], platform=platform)
        if violation["risk_level"] == "red":
            # 重试一次，注入违规信息
            fix_prompt = f"""以下内容存在违规，请修改后重新输出：

违规问题：
{', '.join(v['detail'] for v in violation['issues'])}

原始内容：
{result['text']}

请修复所有违规问题后重新输出完整内容。只输出修正后的JSON。"""
            result = await self._ai_call(fix_prompt, task_type=self.task_type, system=system)
            violation = check_violations(result["text"], platform=platform)

        return {
            "platform": platform,
            "content": result["text"],
            "violation_check": violation,
            "model": result["model"],
        }

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        violation = output.get("violation_check", {})
        has_content = len(output.get("content", "")) > 100
        no_red_violation = violation.get("risk_level") != "red"

        confidence = 0.8 if (has_content and no_red_violation) else 0.3
        return {"confidence": confidence}

    def _build_product_info(self, ctx: AgentContext) -> str:
        parts = []
        keyword = ctx.task_input.get("keyword", "")
        if keyword:
            parts.append(f"关键词：{keyword}")

        # 从选品结果中提取信息
        selection = ctx.task_input.get("product_selection", "")
        if selection:
            parts.append(f"选品方案：\n{selection[:1000]}")

        ai_analysis = ctx.task_input.get("ai_analysis", "")
        if ai_analysis:
            parts.append(f"市场分析摘要：\n{ai_analysis[:500]}")

        return "\n".join(parts) if parts else f"产品关键词：{keyword}"


class DouyinContentAgent(_PlatformContentAgent):
    agent_type = "content_douyin"
    prompt_module = content_douyin
    task_type = "content_social"


class XHSContentAgent(_PlatformContentAgent):
    agent_type = "content_xhs"
    prompt_module = content_xiaohongshu
    task_type = "content_social"


class TaobaoContentAgent(_PlatformContentAgent):
    agent_type = "content_taobao"
    prompt_module = content_taobao
    task_type = "content_formal"


class PDDContentAgent(_PlatformContentAgent):
    agent_type = "content_pdd"
    prompt_module = content_pdd
    task_type = "content_formal"
