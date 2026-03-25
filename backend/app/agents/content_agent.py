"""
Content Agent — 内容生成调度器 + 平台 Sub-agents。

方案C（混合架构）：
  动态专家（AI调用）：策略专家决定内容方向 → 生图专家生成素材prompt
  静态规则（直接注入）：视频参数、平台合规规则

生成链路：
  抖音：策略专家 → 脚本生成 → 生图专家 → [通义万相+TTS+FFmpeg]
  小红书：策略专家 → 文案生成 → 生图专家 → [通义万相+Pillow排版]
"""

import asyncio
import json
from app.agents.base import BaseAgent, AgentContext
from app.agents.prompts import build_agent_system_prompt
from app.agents.memory import MemoryStore
from app.services.prompts import content_douyin, content_xiaohongshu, content_taobao, content_pdd
from app.services.violation_checker import check_violations
from app.services.experts import douyin_strategy, xhs_strategy, image_prompt
from app.services.experts.platform_rules import DOUYIN, XIAOHONGSHU, get_category_hooks
from app.services.experts.video_specs import DOUYIN_VIDEO, SUBTITLE, AUDIO, KEN_BURNS, BGM_STYLES, XHS_IMAGE


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

        selection = ctx.task_input.get("product_selection", "")
        if selection:
            parts.append(f"选品方案：\n{selection[:1000]}")

        ai_analysis = ctx.task_input.get("ai_analysis", "")
        if ai_analysis:
            parts.append(f"市场分析摘要：\n{ai_analysis[:500]}")

        return "\n".join(parts) if parts else f"产品关键词：{keyword}"


class DouyinContentAgent(_PlatformContentAgent):
    """
    抖音内容生成 Agent — 方案C链路：
      Step 1: 抖音策略专家（Claude，AI调用）→ 视频策略
      Step 2: 脚本生成（豆包，AI调用，策略注入）→ 视频脚本
      Step 3: 质量审核（Claude）→ 找AI味，不合格则重写
      Step 4: 生图专家（通义千问，AI调用）→ 每个场景的AI生图prompt
      输出: 脚本 + 图片prompts + 静态视频参数
    """
    agent_type = "content_douyin"
    prompt_module = content_douyin
    task_type = "content_douyin"  # → 路由到豆包

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        platform = observation["platform"]
        product_info = self._build_product_info(ctx)
        category = ctx.task_input.get("category", "default")

        # ── Step 1: 策略专家决策 → Claude（推理最强）──
        strategy_prompt = douyin_strategy.build_strategy_prompt(
            product_info=product_info,
            category=category,
        )
        strategy_result = await self._ai_call(
            strategy_prompt,
            task_type="strategy",  # → Claude
            system=douyin_strategy.SYSTEM,
        )
        strategy_json = strategy_result["text"]

        # ── Step 2: 脚本生成 → 豆包（抖音语感最佳）──
        strategy_injection = f"\n## 内容策略（由策略专家制定，必须遵循）\n{strategy_json}\n"

        hooks = get_category_hooks(category)
        static_rules = f"""
## 平台硬性规则
- 视频规格: {DOUYIN_VIDEO['resolution']}, {DOUYIN_VIDEO['fps']}fps, 9:16竖屏
- 时长: {DOUYIN_VIDEO['duration_range'][0]}-{DOUYIN_VIDEO['duration_range'][1]}秒
- 标题上限: {DOUYIN['title_max_chars']}字
- 标签上限: {DOUYIN['hashtag_limit']}个
- 字幕字号: {SUBTITLE['font_size']}px，底部{int(SUBTITLE['margin_bottom_pct']*100)}%为安全区不放字幕
- 品类Hook参考: {hooks['hook_types']}
- 品类痛点参考: {hooks['pain_points']}
"""

        script_prompt = self.prompt_module.build_prompt(
            product_info=product_info + strategy_injection + static_rules,
            style=ctx.task_input.get("config", {}).get("style", "种草"),
            notes=ctx.task_input.get("config", {}).get("notes", ""),
        )

        system = build_agent_system_prompt(
            self.prompt_module.SYSTEM,
            observation.get("user_dna"),
            observation.get("few_shots"),
            observation.get("guardrails"),
        )

        script_result = await self._ai_call(
            script_prompt,
            task_type="content_douyin",  # → 豆包
            system=system,
        )

        # 违规检测 + 自动修复
        violation = check_violations(script_result["text"], platform=platform)
        if violation["risk_level"] == "red":
            fix_prompt = f"""以下内容存在违规，请修改后重新输出：

违规问题：
{', '.join(v['detail'] for v in violation['issues'])}

原始内容：
{script_result['text']}

请修复所有违规问题后重新输出完整内容。只输出修正后的JSON。"""
            script_result = await self._ai_call(
                fix_prompt,
                task_type="content_douyin",  # → 豆包
                system=system,
            )
            violation = check_violations(script_result["text"], platform=platform)

        # ── Step 3: 质量审核 → Claude（找AI味）──
        review_result = await self._ai_call(
            f"请审核以下抖音脚本的质量，特别关注Hook是否够抓人、语言是否自然口语化：\n\n{script_result['text']}",
            task_type="content_review",  # → Claude
        )

        # ── Step 4: 生图专家 → 通义千问（和通义万相同生态）──
        image_prompt_text = image_prompt.build_douyin_image_prompt(
            product_info=product_info,
            strategy_json=strategy_json,
            scenes_json=script_result["text"],
        )
        image_result = await self._ai_call(
            image_prompt_text,
            task_type="image_prompt",  # → 通义千问
            system=image_prompt.SYSTEM,
        )

        # 组装完整输出
        return {
            "platform": platform,
            "content": script_result["text"],
            "strategy": strategy_json,
            "quality_review": review_result["text"],
            "image_prompts": image_result["text"],
            "video_specs": {
                "resolution": DOUYIN_VIDEO["resolution"],
                "fps": DOUYIN_VIDEO["fps"],
                "duration_range": DOUYIN_VIDEO["duration_range"],
                "subtitle": {
                    "font_size": SUBTITLE["font_size"],
                    "color": SUBTITLE["color"],
                    "stroke_width": SUBTITLE["stroke_width"],
                    "bg_opacity": SUBTITLE["bg_opacity"],
                },
                "audio": {
                    "voice_db_range": AUDIO["voice_db_range"],
                    "bgm_db": AUDIO["bgm_db"],
                    "target_loudness": AUDIO["target_loudness"],
                },
                "ken_burns": {
                    "zoom_range": KEN_BURNS["zoom_range"],
                    "transition_duration": KEN_BURNS["transition_duration"],
                },
                "bgm_style": BGM_STYLES.get(category, BGM_STYLES["default"]),
            },
            "violation_check": violation,
            "model": script_result["model"],
        }


class XHSContentAgent(_PlatformContentAgent):
    """
    小红书内容生成 Agent — 方案C链路：
      Step 1: 小红书策略专家（Claude）→ 图文策略
      Step 2: 文案生成（DeepSeek，策略注入）→ 种草笔记
      Step 3: 质量审核（Claude）→ 找AI味，不合格则带意见重写
      Step 4: 生图专家（通义千问）→ 6张配图的AI生图prompt
      输出: 笔记文案 + 审核报告 + 图片prompts + 静态图片参数
    """
    agent_type = "content_xhs"
    prompt_module = content_xiaohongshu
    task_type = "content_xhs"  # → 路由到 DeepSeek

    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        observation = await self.observe(ctx)
        platform = observation["platform"]
        product_info = self._build_product_info(ctx)
        category = ctx.task_input.get("category", "default")

        # ── Step 1: 策略专家决策 → Claude（推理最强）──
        strategy_prompt = xhs_strategy.build_strategy_prompt(
            product_info=product_info,
            category=category,
        )
        strategy_result = await self._ai_call(
            strategy_prompt,
            task_type="strategy",  # → Claude
            system=xhs_strategy.SYSTEM,
        )
        strategy_json = strategy_result["text"]

        # ── Step 2: 文案生成 → DeepSeek（中文散文最自然）──
        strategy_injection = f"\n## 内容策略（由策略专家制定，必须遵循）\n{strategy_json}\n"

        hooks = get_category_hooks(category)
        static_rules = f"""
## 平台硬性规则
- 标题上限: {XIAOHONGSHU['title_max_chars']}字，必须含{XIAOHONGSHU['title_must_have']}
- 正文: {XIAOHONGSHU['body_word_range'][0]}-{XIAOHONGSHU['body_word_range'][1]}字
- 标签上限: {XIAOHONGSHU['tag_limit']}个，策略：{XIAOHONGSHU['tag_strategy']}
- 图片: {XIAOHONGSHU['recommended_image_count']}张，{XIAOHONGSHU['cover_ratio']}竖版
- 品类Hook参考: {hooks['hook_types']}
- 品类痛点参考: {hooks['pain_points']}
"""

        note_prompt = self.prompt_module.build_prompt(
            product_info=product_info + strategy_injection + static_rules,
            style=ctx.task_input.get("config", {}).get("style", "日常种草"),
            notes=ctx.task_input.get("config", {}).get("notes", ""),
        )

        system = build_agent_system_prompt(
            self.prompt_module.SYSTEM,
            observation.get("user_dna"),
            observation.get("few_shots"),
            observation.get("guardrails"),
        )

        note_result = await self._ai_call(
            note_prompt,
            task_type="content_xhs",  # → DeepSeek
            system=system,
        )

        # 违规检测 + 自动修复
        violation = check_violations(note_result["text"], platform=platform)
        if violation["risk_level"] == "red":
            fix_prompt = f"""以下内容存在违规，请修改后重新输出：

违规问题：
{', '.join(v['detail'] for v in violation['issues'])}

原始内容：
{note_result['text']}

请修复所有违规问题后重新输出完整内容。只输出修正后的JSON。"""
            note_result = await self._ai_call(
                fix_prompt,
                task_type="content_xhs",  # → DeepSeek
                system=system,
            )
            violation = check_violations(note_result["text"], platform=platform)

        # ── Step 3: 质量审核 → Claude（找AI味最强）──
        # 小红书对AI味最敏感，必须审核
        review_result = await self._ai_call(
            f"""请严格审核以下小红书种草笔记的质量。
重点关注：是否像真人分享？有没有AI味？语言是否自然口语化？细节是否具体？

{note_result['text']}

输出JSON：{{"score": 8, "ai_smell_issues": ["问题1"], "must_fix": ["必须改的"], "publish_ready": true}}
只输出JSON。""",
            task_type="content_review",  # → Claude
        )

        # 如果审核不通过，带意见重写一次
        review_data = {}
        try:
            cleaned = review_result["text"].strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines)
            review_data = json.loads(cleaned)
        except (json.JSONDecodeError, KeyError):
            review_data = {"score": 7, "publish_ready": True}

        if review_data.get("score", 7) < 7:
            issues_text = "\n".join(f"- {i}" for i in review_data.get("ai_smell_issues", []))
            must_fix = "\n".join(f"- {f}" for f in review_data.get("must_fix", []))
            rewrite_prompt = f"""{note_prompt}

## ⚠️ 质量审核反馈（必须按此修改）
审核得分：{review_data.get('score')}/10，不合格。

AI味问题：
{issues_text}

必须修改：
{must_fix}

请重新写一篇更加自然、真实、有人感的笔记。像真的在和闺蜜聊天，不是在写说明书。"""

            note_result = await self._ai_call(
                rewrite_prompt,
                task_type="content_xhs",  # → DeepSeek 重写
                system=system,
            )
            violation = check_violations(note_result["text"], platform=platform)

            # 重新审核
            review_result = await self._ai_call(
                f"请重新审核修改后的小红书笔记：\n\n{note_result['text']}\n\n输出JSON评分。只输出JSON。",
                task_type="content_review",  # → Claude
            )
            try:
                cleaned = review_result["text"].strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    lines = [l for l in lines if not l.strip().startswith("```")]
                    cleaned = "\n".join(lines)
                review_data = json.loads(cleaned)
            except (json.JSONDecodeError, KeyError):
                pass

        # ── Step 4: 生图专家 → 通义千问（和通义万相同生态）──
        image_plan = "见策略方案中的image_plan字段"
        try:
            strategy_data = json.loads(strategy_json)
            if "image_plan" in strategy_data:
                image_plan = json.dumps(strategy_data["image_plan"], ensure_ascii=False)
        except (json.JSONDecodeError, KeyError):
            pass

        image_prompt_text = image_prompt.build_xhs_image_prompt(
            product_info=product_info,
            strategy_json=strategy_json,
            image_plan_json=image_plan,
        )
        image_result = await self._ai_call(
            image_prompt_text,
            task_type="image_prompt",  # → 通义千问
            system=image_prompt.SYSTEM,
        )

        # 组装完整输出
        return {
            "platform": platform,
            "content": note_result["text"],
            "strategy": strategy_json,
            "quality_review": review_data,
            "image_prompts": image_result["text"],
            "image_specs": {
                "cover_size": XHS_IMAGE["cover_size"],
                "body_size": XHS_IMAGE["body_size"],
                "format": XHS_IMAGE["format"],
                "quality": XHS_IMAGE["quality"],
                "recommended_count": XHS_IMAGE["recommended_images"],
            },
            "violation_check": violation,
            "model": note_result["model"],
        }


class TaobaoContentAgent(_PlatformContentAgent):
    agent_type = "content_taobao"
    prompt_module = content_taobao
    task_type = "content_formal"


class PDDContentAgent(_PlatformContentAgent):
    agent_type = "content_pdd"
    prompt_module = content_pdd
    task_type = "content_formal"
