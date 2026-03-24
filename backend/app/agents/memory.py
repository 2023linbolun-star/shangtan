"""
MemoryStore — Agent 进化系统的数据读写层。
管理 User DNA、Few-shot 案例库、失败教训、执行记录。
"""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentMemory, UserDNA, FewShotExample, FailurePattern


class MemoryStore:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── User DNA ──

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
        content_fields = {"preferred_tone", "avoid_patterns", "content_preferences", "preferred_platforms"}
        scout_fields = {"risk_tolerance", "min_margin", "preferred_price_band", "avoid_categories"}

        for key, value in updates.items():
            if key in store_fields:
                if not dna.store_profile:
                    dna.store_profile = {}
                dna.store_profile[key] = value
            elif key in content_fields:
                if not dna.content_preferences:
                    dna.content_preferences = {}
                dna.content_preferences[key] = value
            elif key in scout_fields:
                if not dna.scout_preferences:
                    dna.scout_preferences = {}
                dna.scout_preferences[key] = value

        dna.interaction_count = (dna.interaction_count or 0) + 1
        dna.last_updated = datetime.now(timezone.utc)
        dna.version = (dna.version or 0) + 1
        await self.db.flush()

    # ── Few-Shot Examples ──

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

    # ── Failure Guardrails ──

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

    # ── Execution Records ──

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
