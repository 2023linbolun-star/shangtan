"""
LearningEngine — 处理用户反馈，驱动 Agent 自我进化。

反馈来源:
1. 显式: 👍/👎 按钮
2. 隐式-编辑: 用户修改 AI 输出（编辑距离 > 0.3 = 不满意）
3. 隐式-拒绝: 用户拒绝并要求重新生成
4. 显式-文字: 用户写出修改意见
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.memory import MemoryStore
from app.db.models import AgentMemory, UserDNA, FewShotExample
from app.services.ai_engine import ai_analyze_full

logger = logging.getLogger("shangtanai.learning")


class LearningEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.store = MemoryStore(db)

    async def process_feedback(
        self,
        user_id: str,
        memory_id: str,
        feedback_score: int,  # -1, 0, 1
        user_edits: dict | None = None,
        original_output: dict | None = None,
        feedback_text: str | None = None,
    ):
        """处理一条反馈，更新所有进化状态。"""

        # 1. 更新执行记录
        memory = await self.db.get(AgentMemory, memory_id)
        if not memory:
            return

        edit_distance = None
        if user_edits and original_output:
            edit_distance = self._compute_edit_distance(original_output, user_edits)

        await self.store.update_feedback(
            memory_id=memory_id,
            feedback_score=feedback_score,
            edit_distance=edit_distance,
            feedback_notes=feedback_text,
        )

        agent_type = memory.agent_type

        # 2. 正面反馈 + 低编辑幅度 → 存为优秀案例
        if feedback_score == 1 and (edit_distance is None or edit_distance < 0.2):
            await self._maybe_add_few_shot(user_id, agent_type, memory)

        # 3. 负面反馈或大幅编辑 → 提取失败模式
        if feedback_score == -1 or (edit_distance is not None and edit_distance > 0.3):
            await self._extract_failure_pattern(
                user_id, agent_type, memory, user_edits, feedback_text
            )

        # 4. 有文字反馈 → 用 AI 更新用户画像
        if feedback_text:
            await self._update_dna_from_feedback(user_id, agent_type, feedback_text)

        await self.db.flush()
        logger.info(f"Feedback processed: user={user_id}, agent={agent_type}, score={feedback_score}")

    async def _maybe_add_few_shot(self, user_id: str, agent_type: str, memory: AgentMemory):
        """将高质量输出存为 few-shot 案例。"""
        # 从 output_summary 中提取 keyword（如果有）
        keyword = ""
        try:
            data = json.loads(memory.output_summary)
            keyword = data.get("keyword", "")
        except (json.JSONDecodeError, AttributeError):
            pass

        await self.store.add_few_shot(
            user_id=user_id,
            agent_type=agent_type,
            keyword=keyword,
            output_summary=memory.output_summary or "",
        )
        logger.info(f"Added few-shot example for {agent_type}")

    async def _extract_failure_pattern(
        self, user_id: str, agent_type: str, memory: AgentMemory,
        user_edits: dict | None, feedback_text: str | None,
    ):
        """用 GLM(免费) 从失败中提取教训。"""
        context_parts = [f"原始输出摘要: {(memory.output_summary or '')[:300]}"]
        if feedback_text:
            context_parts.append(f"用户反馈: {feedback_text}")
        if user_edits:
            context_parts.append(f"用户修改后: {json.dumps(user_edits, ensure_ascii=False)[:300]}")

        prompt = f"""分析以下AI输出被用户否定/大幅修改的原因，用一句中文总结需要避免的模式。

{chr(10).join(context_parts)}

只输出一句话，例如："不要在小红书笔记中使用过多营销语气"
一句话:"""

        result = await ai_analyze_full(prompt, task_type="violation")  # GLM, 免费
        pattern = result["text"].strip().strip('"').strip("'")

        if pattern and len(pattern) > 5:
            await self.store.add_failure_pattern(
                user_id=user_id,
                agent_type=agent_type,
                pattern=pattern,
                source="user_rejection" if memory.was_rejected else "heavy_edit",
            )
            logger.info(f"Extracted failure pattern for {agent_type}: {pattern}")

    async def _update_dna_from_feedback(self, user_id: str, agent_type: str, feedback_text: str):
        """用 AI 从反馈文字中提取偏好更新。"""
        current_dna = await self.store.get_user_dna(user_id)

        prompt = f"""从用户反馈中提取偏好信息，更新用户画像。

当前画像:
{json.dumps(current_dna, ensure_ascii=False) if current_dna else "（新用户）"}

用户反馈: "{feedback_text}"
模块: {agent_type}

输出需要更新的字段（JSON），只输出有变化的字段:
可用字段: store_style, brand_voice, target_audience, price_positioning, preferred_tone, avoid_patterns, risk_tolerance, min_margin, categories, preferred_platforms

只输出JSON，无其他文字。如果反馈中没有偏好信息则输出空对象 {{}}"""

        result = await ai_analyze_full(prompt, task_type="violation")  # GLM, 免费
        try:
            updates = json.loads(result["text"].strip())
            if updates and isinstance(updates, dict):
                await self.store.update_user_dna(user_id, updates)
                logger.info(f"Updated user DNA from feedback: {list(updates.keys())}")
        except (json.JSONDecodeError, TypeError):
            pass

    def _compute_edit_distance(self, original: dict, edited: dict) -> float:
        """计算原始输出和用户编辑版本的差异度 (0.0-1.0)。"""
        orig_text = json.dumps(original, ensure_ascii=False)
        edit_text = json.dumps(edited, ensure_ascii=False)

        max_len = max(len(orig_text), len(edit_text))
        if max_len == 0:
            return 0.0

        # 快速近似：字符级匹配率
        common = sum(1 for a, b in zip(orig_text, edit_text) if a == b)
        return 1.0 - (common / max_len)
