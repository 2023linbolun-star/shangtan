"""
BaseAgent — 所有 Agent 的基类。
实现 观察(Observe) → 思考(Think) → 行动(Act) → 评估(Evaluate) 循环。
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_engine import ai_analyze_full


@dataclass
class AgentContext:
    """Agent 执行的输入上下文。"""
    user_id: str
    pipeline_id: str | None = None
    task_input: dict[str, Any] = field(default_factory=dict)
    user_dna: dict[str, Any] = field(default_factory=dict)
    few_shot_examples: list[dict] = field(default_factory=list)
    failure_guardrails: list[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Agent 执行的输出结果。"""
    agent_id: str
    agent_type: str
    success: bool
    output: dict[str, Any]
    reasoning: str = ""
    confidence: float = 0.5
    ai_calls: list[dict] = field(default_factory=list)
    duration_ms: float = 0.0
    sub_agent_results: list["AgentResult"] = field(default_factory=list)


class BaseAgent(ABC):
    """
    Agent 基类。子类实现 observe/think/act 三个核心方法。

    生命周期:
      1. observe()  — 收集上下文、加载记忆
      2. think()    — 推理决策（可能不需要AI调用）
      3. act()      — 执行任务（AI调用、工具调用、派发Sub-agent）
      4. evaluate() — 自我评估输出质量
    """

    agent_type: str = "base"

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_id = str(uuid.uuid4())[:8]
        self.logger = logging.getLogger(f"shangtanai.agent.{self.agent_type}")
        self._ai_calls: list[dict] = []

    async def run(self, ctx: AgentContext) -> AgentResult:
        """主执行循环。"""
        start = time.perf_counter()

        try:
            observation = await self.observe(ctx)
            plan = await self.think(ctx, observation)
            raw_output = await self.act(ctx, plan)
            evaluation = await self.evaluate(ctx, raw_output)

            duration = round((time.perf_counter() - start) * 1000, 1)

            result = AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                success=True,
                output=raw_output,
                reasoning=plan.get("reasoning", ""),
                confidence=evaluation.get("confidence", 0.5),
                ai_calls=list(self._ai_calls),
                duration_ms=duration,
            )

            await self._record_execution(ctx, result)
            return result

        except Exception as e:
            duration = round((time.perf_counter() - start) * 1000, 1)
            self.logger.error(f"Agent {self.agent_type} failed: {e}")
            await self._record_failure(ctx, str(e))

            return AgentResult(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                success=False,
                output={"error": str(e)},
                reasoning=f"Failed: {e}",
                confidence=0.0,
                ai_calls=list(self._ai_calls),
                duration_ms=duration,
            )

    @abstractmethod
    async def observe(self, ctx: AgentContext) -> dict:
        """收集上下文和环境信息。"""
        ...

    @abstractmethod
    async def think(self, ctx: AgentContext, observation: dict) -> dict:
        """推理决策，返回包含 'reasoning' 键的 dict。"""
        ...

    @abstractmethod
    async def act(self, ctx: AgentContext, plan: dict) -> dict:
        """执行任务，返回输出 dict。"""
        ...

    async def evaluate(self, ctx: AgentContext, output: dict) -> dict:
        """自我评估。默认返回中等置信度，子类可覆盖。"""
        return {"confidence": 0.7, "issues": []}

    # ── AI 调用（带追踪）──

    async def _ai_call(self, prompt: str, task_type: str, system: str | None = None) -> dict:
        result = await ai_analyze_full(prompt, task_type=task_type, system=system)
        self._ai_calls.append({
            "task_type": task_type,
            "model": result.get("model", "unknown"),
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0),
            "cost": result.get("cost", 0.0),
        })
        return result

    # ── Sub-agent ──

    async def _spawn(self, agent_class: type[BaseAgent], ctx: AgentContext) -> AgentResult:
        sub = agent_class(self.db)
        result = await sub.run(ctx)
        return result

    async def _spawn_parallel(
        self, agents_and_contexts: list[tuple[type[BaseAgent], AgentContext]]
    ) -> list[AgentResult]:
        tasks = [cls(self.db).run(ctx) for cls, ctx in agents_and_contexts]
        return await asyncio.gather(*tasks, return_exceptions=False)

    # ── 记忆 ──

    async def _record_execution(self, ctx: AgentContext, result: AgentResult):
        from app.agents.memory import MemoryStore
        store = MemoryStore(self.db)
        total_cost = sum(c.get("cost", 0) for c in result.ai_calls)
        await store.record_execution(
            user_id=ctx.user_id,
            agent_type=self.agent_type,
            task_input_hash=self._hash(ctx.task_input),
            output_summary=self._summarize(result.output),
            confidence=result.confidence,
            duration_ms=result.duration_ms,
            total_cost=total_cost,
            ai_calls=result.ai_calls,
        )

    async def _record_failure(self, ctx: AgentContext, error: str):
        from app.agents.memory import MemoryStore
        store = MemoryStore(self.db)
        await store.record_failure(
            user_id=ctx.user_id,
            agent_type=self.agent_type,
            error=error,
        )

    def _hash(self, data: dict) -> str:
        text = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def _summarize(self, output: dict) -> str:
        text = json.dumps(output, ensure_ascii=False)
        return text[:500] if len(text) > 500 else text
