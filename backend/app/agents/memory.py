"""
MemoryStore — Agent 进化系统的数据读写层。
管理 User DNA、Few-shot 案例库、失败教训、执行记录、偏好学习。
"""

import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentMemory, UserDNA, FewShotExample, FailurePattern

logger = logging.getLogger("shangtanai.agents.memory")


class MemoryStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ══════════════════════════════════════════════════════════
    #  User DNA
    # ══════════════════════════════════════════════════════════

    async def get_user_dna(self, user_id: str) -> dict:
        """加载用户画像。新用户返回空 dict。"""
        result = await self.db.execute(
            select(UserDNA).where(UserDNA.user_id == user_id)
        )
        dna = result.scalar_one_or_none()
        if not dna:
            return {}
        return {
            **(dna.store_profile or {}),
            **(dna.content_preferences or {}),
            **(dna.scout_preferences or {}),
        }

    async def update_user_dna(self, user_id: str, updates: dict):
        """更新用户画像的特定字段。"""
        result = await self.db.execute(
            select(UserDNA).where(UserDNA.user_id == user_id)
        )
        dna = result.scalar_one_or_none()

        if not dna:
            dna = UserDNA(user_id=user_id)
            self.db.add(dna)

        # Route updates to correct jsonb column
        store_fields = {"store_style", "brand_voice", "target_audience", "price_positioning", "categories"}
        content_fields = {
            "preferred_tone", "avoid_patterns", "content_preferences", "preferred_platforms",
            "voice_style", "visual_preference", "hook_preference", "content_length",
            "emoji_usage", "humor_level", "selling_intensity", "category_overrides",
            "preferred_styles",
        }
        scout_fields = {"risk_tolerance", "min_margin", "preferred_price_band", "avoid_categories"}

        for key, value in updates.items():
            if key in store_fields:
                if not dna.store_profile:
                    dna.store_profile = {}
                dna.store_profile[key] = value
            elif key in content_fields:
                if not dna.content_preferences:
                    dna.content_preferences = {}
                # 嵌套字段合并（如 preferred_styles）
                if isinstance(value, dict) and isinstance(dna.content_preferences.get(key), dict):
                    dna.content_preferences[key] = {**dna.content_preferences[key], **value}
                else:
                    dna.content_preferences[key] = value
            elif key in scout_fields:
                if not dna.scout_preferences:
                    dna.scout_preferences = {}
                dna.scout_preferences[key] = value

        dna.interaction_count = (dna.interaction_count or 0) + 1
        dna.last_updated = datetime.now(timezone.utc)
        dna.version = (dna.version or 0) + 1
        await self.db.flush()

    # ══════════════════════════════════════════════════════════
    #  Few-Shot Examples
    # ══════════════════════════════════════════════════════════

    async def get_few_shots(self, user_id: str, agent_type: str, limit: int = 3) -> list[dict]:
        """获取该用户该 Agent 类型的优秀案例。"""
        result = await self.db.execute(
            select(FewShotExample)
            .where(FewShotExample.user_id == user_id, FewShotExample.agent_type == agent_type)
            .order_by(FewShotExample.created_at.desc())
            .limit(limit)
        )
        return [
            {"keyword": ex.keyword, "platform": ex.platform, "output_summary": ex.output_summary}
            for ex in result.scalars().all()
        ]

    async def add_few_shot(self, user_id: str, agent_type: str, keyword: str,
                           output_summary: str, platform: str | None = None):
        """添加一个优秀案例。"""
        example = FewShotExample(
            user_id=user_id,
            agent_type=agent_type,
            keyword=keyword,
            platform=platform,
            output_summary=output_summary[:500],
        )
        self.db.add(example)
        await self.db.flush()

    async def count_few_shots(self, user_id: str) -> int:
        """统计用户的优秀案例总数。"""
        result = await self.db.execute(
            select(func.count(FewShotExample.id))
            .where(FewShotExample.user_id == user_id)
        )
        return result.scalar() or 0

    # ══════════════════════════════════════════════════════════
    #  Failure Guardrails
    # ══════════════════════════════════════════════════════════

    async def get_failure_guardrails(self, user_id: str, agent_type: str) -> list[str]:
        """获取该 Agent 的失败教训列表。"""
        result = await self.db.execute(
            select(FailurePattern)
            .where(FailurePattern.user_id == user_id, FailurePattern.agent_type == agent_type)
            .order_by(FailurePattern.occurrence_count.desc())
            .limit(5)
        )
        return [p.pattern_description for p in result.scalars().all()]

    async def add_failure_pattern(self, user_id: str, agent_type: str,
                                  pattern: str, source: str = "user_rejection"):
        """添加或更新失败模式。相同模式则增加计数。"""
        result = await self.db.execute(
            select(FailurePattern).where(
                FailurePattern.user_id == user_id,
                FailurePattern.agent_type == agent_type,
                FailurePattern.pattern_description == pattern,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.occurrence_count += 1
            existing.last_seen = datetime.now(timezone.utc)
        else:
            self.db.add(FailurePattern(
                user_id=user_id,
                agent_type=agent_type,
                pattern_description=pattern,
                source=source,
            ))
        await self.db.flush()

    async def count_failure_patterns(self, user_id: str) -> int:
        """统计用户的失败教训总数。"""
        result = await self.db.execute(
            select(func.count(FailurePattern.id))
            .where(FailurePattern.user_id == user_id)
        )
        return result.scalar() or 0

    # ══════════════════════════════════════════════════════════
    #  偏好学习（从反馈中自动学习）
    # ══════════════════════════════════════════════════════════

    async def learn_from_feedback(
        self,
        user_id: str,
        agent_type: str,
        content_text: str,
        feedback_score: int,
        edit_notes: str | None = None,
    ) -> dict:
        """
        从用户反馈中自动学习偏好。

        Returns:
            {
                "action": "preference_updated" | "example_added" | "guardrail_added",
                "message": "AI已记录：...",
                "details": {...}
            }
        """
        learned = {"action": "acknowledged", "message": "反馈已记录", "details": {}}

        if feedback_score == 1:  # 👍
            # 加入 few-shot 案例库
            keyword = content_text[:50].replace("\n", " ")
            await self.add_few_shot(
                user_id=user_id,
                agent_type=agent_type,
                keyword=keyword,
                output_summary=content_text[:500],
            )

            # 分析内容风格特征并强化偏好
            style_signal = self._extract_style_signal(content_text)
            if style_signal:
                await self._reinforce_preference(user_id, style_signal)
                learned = {
                    "action": "example_added",
                    "message": f"AI已学习：你认可这种风格，已加入案例库（共{await self.count_few_shots(user_id)}条）",
                    "details": {"style_signal": style_signal},
                }
            else:
                learned = {
                    "action": "example_added",
                    "message": "AI已记住这条优秀内容，下次会参考类似风格",
                    "details": {},
                }

        elif feedback_score == -1:  # 👎
            # 加入失败教训
            if edit_notes:
                # 用户写了修改意见，直接用作教训
                await self.add_failure_pattern(
                    user_id=user_id,
                    agent_type=agent_type,
                    pattern=edit_notes[:200],
                    source="user_feedback",
                )
                # 提取偏好信号
                avoid_signal = self._extract_avoid_signal(edit_notes)
                if avoid_signal:
                    await self._add_avoid_pattern(user_id, avoid_signal)

                learned = {
                    "action": "guardrail_added",
                    "message": f"AI已记录：{edit_notes[:50]}，下次会避免",
                    "details": {"avoid_signal": avoid_signal},
                }
            else:
                # 没有修改意见，记录通用不满
                await self.add_failure_pattern(
                    user_id=user_id,
                    agent_type=agent_type,
                    pattern="用户对此次输出不满意（未说明原因）",
                    source="user_rejection",
                )
                learned = {
                    "action": "guardrail_added",
                    "message": "AI已记录你不满意这次结果，建议写下修改意见帮助AI更好学习",
                    "details": {},
                }

        return learned

    def _extract_style_signal(self, content: str) -> str:
        """从内容中提取风格信号（简单启发式）。"""
        signals = []
        if "！" in content and content.count("！") > 3:
            signals.append("活泼语气")
        if "~" in content or "～" in content:
            signals.append("轻松可爱")
        if any(w in content for w in ["测试", "实测", "对比", "评分"]):
            signals.append("测评风格")
        if any(w in content for w in ["姐妹", "宝子", "家人们"]):
            signals.append("亲切口语")
        if content.count("\n") > 10:
            signals.append("长篇详细")
        return "、".join(signals) if signals else ""

    def _extract_avoid_signal(self, notes: str) -> str:
        """从用户修改意见中提取回避信号。"""
        # 提取常见的不满表达
        avoid_keywords = {
            "太长": "内容过长",
            "太短": "内容太短",
            "太假": "不够真实",
            "太硬": "推销感太重",
            "ai味": "AI味太重",
            "不自然": "表达不自然",
            "夸张": "语气过于夸张",
            "感叹号": "感叹号过多",
            "emoji": "emoji使用不当",
            "广告": "广告感太强",
            "模板": "模板感太重",
        }
        for keyword, signal in avoid_keywords.items():
            if keyword in notes.lower():
                return signal
        return notes[:50] if notes else ""

    async def _reinforce_preference(self, user_id: str, style_signal: str):
        """强化用户的正向偏好。"""
        result = await self.db.execute(
            select(UserDNA).where(UserDNA.user_id == user_id)
        )
        dna = result.scalar_one_or_none()
        if not dna:
            return

        if not dna.content_preferences:
            dna.content_preferences = {}

        # 记录风格信号历史
        history = dna.content_preferences.get("learned_style_signals", [])
        history.append({
            "signal": style_signal,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        # 只保留最近20条
        dna.content_preferences["learned_style_signals"] = history[-20:]
        await self.db.flush()

    async def _add_avoid_pattern(self, user_id: str, pattern: str):
        """添加用户回避模式。"""
        result = await self.db.execute(
            select(UserDNA).where(UserDNA.user_id == user_id)
        )
        dna = result.scalar_one_or_none()
        if not dna:
            return

        if not dna.content_preferences:
            dna.content_preferences = {}

        avoid_list = dna.content_preferences.get("avoid_patterns", [])
        if pattern not in avoid_list:
            avoid_list.append(pattern)
            dna.content_preferences["avoid_patterns"] = avoid_list[-10:]  # 最多10条
            await self.db.flush()

    # ══════════════════════════════════════════════════════════
    #  记忆统计（AI记忆面板数据）
    # ══════════════════════════════════════════════════════════

    async def get_memory_stats(self, user_id: str) -> dict:
        """获取用户的AI记忆统计。"""
        # UserDNA
        dna_result = await self.db.execute(
            select(UserDNA).where(UserDNA.user_id == user_id)
        )
        dna = dna_result.scalar_one_or_none()

        # 偏好条数
        prefs = dna.content_preferences if dna else {}
        pref_count = sum(1 for k, v in prefs.items() if v and k not in (
            "learned_style_signals", "preferred_styles", "category_overrides"
        ))

        # few-shot案例数
        few_shot_count = await self.count_few_shots(user_id)

        # 失败教训数
        guardrail_count = await self.count_failure_patterns(user_id)

        # 交互次数
        interaction_count = dna.interaction_count if dna else 0

        # 学习天数（从创建到现在）
        days_learning = 0
        if dna and dna.created_at:
            delta = datetime.now(timezone.utc) - dna.created_at
            days_learning = max(1, delta.days)

        # 采纳率（最近50次的👍比例）
        exec_result = await self.db.execute(
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .order_by(AgentMemory.created_at.desc())
            .limit(50)
        )
        memories = exec_result.scalars().all()
        total_with_feedback = sum(1 for m in memories if m.feedback_score is not None)
        positive_feedback = sum(1 for m in memories if m.feedback_score and m.feedback_score > 0)
        adoption_rate = round(positive_feedback / max(total_with_feedback, 1) * 100)

        # 已学习的偏好列表（可编辑/删除）
        learned_preferences = []
        field_labels = {
            "voice_style": "语气风格",
            "visual_preference": "视觉风格",
            "hook_preference": "开头偏好",
            "content_length": "内容长度",
            "selling_intensity": "推销强度",
        }
        for key, label in field_labels.items():
            val = prefs.get(key)
            if val:
                learned_preferences.append({"key": key, "label": label, "value": val, "source": "user_set"})

        avoid_patterns = prefs.get("avoid_patterns", [])
        for p in avoid_patterns:
            learned_preferences.append({"key": "avoid", "label": "回避", "value": p, "source": "learned"})

        return {
            "days_learning": days_learning,
            "interaction_count": interaction_count,
            "preference_count": pref_count,
            "few_shot_count": few_shot_count,
            "guardrail_count": guardrail_count,
            "adoption_rate": adoption_rate,
            "total_feedbacks": total_with_feedback,
            "learned_preferences": learned_preferences,
            "preferred_styles": prefs.get("preferred_styles", {}),
        }

    # ══════════════════════════════════════════════════════════
    #  执行记录
    # ══════════════════════════════════════════════════════════

    async def record_execution(self, user_id: str, agent_type: str, **kwargs):
        """记录一次 Agent 执行。"""
        memory = AgentMemory(user_id=user_id, agent_type=agent_type, **kwargs)
        self.db.add(memory)
        await self.db.flush()
        return memory.id

    async def record_failure(self, user_id: str, agent_type: str, error: str):
        """记录一次失败。"""
        memory = AgentMemory(
            user_id=user_id,
            agent_type=agent_type,
            task_input_hash="error",
            output_summary=f"FAILED: {error[:400]}",
            confidence=0.0,
            duration_ms=0,
            total_cost=0,
            was_rejected=True,
        )
        self.db.add(memory)
        await self.db.flush()

    async def update_feedback(self, memory_id: str, feedback_score: int,
                              edit_distance: float | None = None,
                              feedback_notes: str | None = None):
        """更新某次执行的用户反馈。"""
        memory = await self.db.get(AgentMemory, memory_id)
        if memory:
            memory.feedback_score = feedback_score
            memory.edit_distance = edit_distance
            memory.feedback_notes = feedback_notes
            if feedback_score == -1:
                memory.was_rejected = True
            await self.db.flush()

    # ══════════════════════════════════════════════════════════
    #  Prompt 编辑学习（从用户对prompt的修改中学习视觉偏好）
    # ══════════════════════════════════════════════════════════

    async def learn_from_prompt_edit(
        self,
        user_id: str,
        original_prompt: str,
        edited_prompt: str,
        context: dict | None = None,
    ) -> dict:
        """
        从用户对生图prompt的编辑中学习视觉偏好。

        Uses GLM (free, via ai_analyze_full with task_type="violation") to diff
        the two prompts and extract preference signals.

        Args:
            user_id: user identifier
            original_prompt: AI-generated original prompt
            edited_prompt: user-edited version of the prompt
            context: optional context dict (e.g. style, product_info)

        Returns:
            {
                "action": "visual_preference_learned",
                "added_elements": [...],
                "removed_elements": [...],
                "style_shift": "...",
                "preference_signal": "..."
            }
        """
        from app.services.ai_engine import ai_analyze_full

        context = context or {}

        # Use GLM (free) to analyze the diff between original and edited prompts
        diff_prompt = (
            f"对比以下两个生图prompt，分析用户的编辑意图。\n\n"
            f"原始prompt：{original_prompt}\n\n"
            f"用户修改后：{edited_prompt}\n\n"
            f"请输出JSON格式：\n"
            f'{{"added_elements": ["用户新增的元素"], '
            f'"removed_elements": ["用户删除的元素"], '
            f'"style_shift": "风格变化方向描述（如：从商业感转向生活感）", '
            f'"preference_signal": "一句话总结用户的视觉偏好倾向"}}\n\n'
            f"只输出JSON。"
        )

        try:
            result = await ai_analyze_full(diff_prompt, task_type="violation")
            raw_text = result.get("text", "{}").strip()
            # Clean markdown code blocks
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw_text = "\n".join(lines)
            diff_data = json.loads(raw_text)
        except Exception as e:
            logger.warning(f"Failed to analyze prompt edit diff: {e}")
            diff_data = {
                "added_elements": [],
                "removed_elements": [],
                "style_shift": "",
                "preference_signal": "",
            }

        added = diff_data.get("added_elements", [])
        removed = diff_data.get("removed_elements", [])
        style_shift = diff_data.get("style_shift", "")
        preference_signal = diff_data.get("preference_signal", "")

        # Store preference_signal in UserDNA via visual_preferences
        if preference_signal:
            visual_prefs = {
                "visual_preference": preference_signal,
            }
            if style_shift:
                visual_prefs["preferred_color_tone"] = style_shift
            await self.update_user_dna(user_id, visual_prefs)

        # Store removed_elements as FailurePattern entries
        for elem in removed:
            if elem:
                await self.add_failure_pattern(
                    user_id=user_id,
                    agent_type="scene_architect",
                    pattern=f"用户不喜欢生图中出现: {elem}",
                    source="prompt_edit",
                )

        # Store the edited version as a FewShotExample
        if edited_prompt and edited_prompt != original_prompt:
            keyword = context.get("product_info", edited_prompt[:50])
            await self.add_few_shot(
                user_id=user_id,
                agent_type="scene_architect",
                keyword=keyword[:50],
                output_summary=edited_prompt[:500],
                platform=context.get("platform"),
            )

        return {
            "action": "visual_preference_learned",
            "added_elements": added,
            "removed_elements": removed,
            "style_shift": style_shift,
            "preference_signal": preference_signal,
        }
