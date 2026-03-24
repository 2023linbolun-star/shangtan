"""
Orchestrator Agent — 总调度，替代 PipelineEngine。
编排各 Agent 的执行顺序，管理审批门，处理异常。
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Pipeline, PipelineStep, PipelineStatus, StepStatus, StepType,
)
from app.services.event_bus import event_bus
from app.agents.base import AgentContext
from app.agents.memory import MemoryStore
from app.agents.scout_agent import ScoutAgent
from app.agents.content_agent import ContentAgent
from app.agents.listing_agent import ListingAgent
from app.agents.publish_agent import PublishAgent
from app.agents.trend_scan_agent import TrendScanAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.order_monitor_agent import OrderMonitorAgent
from app.agents.ad_agent import AdAgent

logger = logging.getLogger("shangtanai.orchestrator")

# Agent 注册表
AGENT_MAP = {
    StepType.scout: ScoutAgent,
    StepType.product_selection: ScoutAgent,  # 复用 Scout Agent，prompt 不同
    StepType.content: ContentAgent,
    StepType.publish_schedule: PublishAgent,
    StepType.trend_scan: TrendScanAgent,
    StepType.supplier_match: SupplierAgent,
    StepType.performance_review: PerformanceAgent,
    StepType.order_monitor: OrderMonitorAgent,
    StepType.ad_create: AdAgent,
}

# 需要人工审批的步骤
APPROVAL_REQUIRED = {StepType.product_selection, StepType.content, StepType.supplier_match}


class OrchestratorAgent:
    """Pipeline 总调度。"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, pipeline_id: str):
        """执行 Pipeline，逐步调度 Agent。"""
        pipeline = await self._load_pipeline(pipeline_id)
        if not pipeline:
            logger.error(f"Pipeline {pipeline_id} not found")
            return

        pipeline.status = PipelineStatus.running
        await self.db.flush()

        # 加载用户进化数据
        store = MemoryStore(self.db)
        user_dna = await store.get_user_dna(pipeline.user_id)

        accumulated = {
            "keyword": pipeline.trigger_keyword,
            "platforms": pipeline.target_platforms,
            "config": pipeline.config or {},
        }

        for step in sorted(pipeline.steps, key=lambda s: s.step_order):
            # 跳过已完成的步骤（resume after approval）
            if step.status == StepStatus.completed:
                if step.output_data:
                    accumulated = {**accumulated, **step.output_data}
                continue

            if step.status in (StepStatus.skipped, StepStatus.awaiting_approval):
                if step.status == StepStatus.awaiting_approval:
                    pipeline.status = PipelineStatus.paused
                    await self.db.flush()
                    return
                continue

            # 获取对应 Agent
            agent_class = AGENT_MAP.get(step.step_type)
            if not agent_class:
                logger.error(f"No agent for step type: {step.step_type}")
                step.status = StepStatus.failed
                step.error_message = f"未知步骤类型: {step.step_type}"
                await self.db.flush()
                continue

            # 标记运行中
            step.status = StepStatus.running
            step.started_at = datetime.now(timezone.utc)
            step.input_data = accumulated
            await self.db.flush()

            await event_bus.emit("pipeline.step.started", {
                "pipeline_id": pipeline_id,
                "step_type": step.step_type.value,
            })

            # 构建 Agent 上下文
            ctx = AgentContext(
                user_id=pipeline.user_id,
                pipeline_id=pipeline_id,
                task_input=accumulated,
                user_dna=user_dna,
                few_shot_examples=await store.get_few_shots(pipeline.user_id, step.step_type.value),
                failure_guardrails=await store.get_failure_guardrails(pipeline.user_id, step.step_type.value),
            )

            # 执行 Agent
            agent = agent_class(self.db)
            result = await agent.run(ctx)

            step.completed_at = datetime.now(timezone.utc)

            if not result.success:
                step.status = StepStatus.failed
                step.error_message = result.output.get("error", "Unknown error")
                step.output_data = result.output
                pipeline.status = PipelineStatus.failed
                await self.db.flush()

                await event_bus.emit("pipeline.step.failed", {
                    "pipeline_id": pipeline_id,
                    "step_type": step.step_type.value,
                    "error": step.error_message,
                })
                return

            step.output_data = result.output

            # 检查是否需要审批
            if step.step_type in APPROVAL_REQUIRED:
                step.status = StepStatus.awaiting_approval
                pipeline.status = PipelineStatus.paused
                await self.db.flush()

                await event_bus.emit("pipeline.step.awaiting_approval", {
                    "pipeline_id": pipeline_id,
                    "step_type": step.step_type.value,
                })
                return
            else:
                step.status = StepStatus.completed
                accumulated = {**accumulated, **result.output}

            await self.db.flush()
            await event_bus.emit("pipeline.step.completed", {
                "pipeline_id": pipeline_id,
                "step_type": step.step_type.value,
            })

        # 全部完成
        pipeline.status = PipelineStatus.completed
        await self.db.flush()
        await event_bus.emit("pipeline.completed", {"pipeline_id": pipeline_id})

    async def approve_step(self, pipeline_id: str, step_id: str, edits: dict | None = None):
        """审批通过某步骤，然后继续执行。"""
        step = await self.db.get(PipelineStep, step_id)
        if not step or step.pipeline_id != pipeline_id:
            raise ValueError("步骤不存在")
        if step.status != StepStatus.awaiting_approval:
            raise ValueError(f"该步骤不在审批状态 (当前: {step.status})")

        if edits and step.output_data:
            step.output_data = {**step.output_data, **edits}

        step.status = StepStatus.completed
        await self.db.flush()

        # 继续执行后续步骤
        await self.run(pipeline_id)

    async def retry_step(self, pipeline_id: str, step_id: str):
        """重试失败的步骤。"""
        step = await self.db.get(PipelineStep, step_id)
        if not step or step.pipeline_id != pipeline_id:
            raise ValueError("步骤不存在")

        step.status = StepStatus.pending
        step.error_message = None
        step.output_data = None
        await self.db.flush()

        await self.run(pipeline_id)

    async def _load_pipeline(self, pipeline_id: str) -> Pipeline | None:
        result = await self.db.execute(
            select(Pipeline)
            .where(Pipeline.id == pipeline_id)
            .options(selectinload(Pipeline.steps))
        )
        return result.scalar_one_or_none()
