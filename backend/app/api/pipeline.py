"""
Pipeline API — 创建、执行、查询、审批流水线。
"""

import asyncio
import json
import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.engine import get_db, async_session
from app.db.models import (
    Pipeline, PipelineStep, PipelineStatus, StepStatus, StepType, User,
)
from app.middleware.auth import get_current_user
from app.agents.orchestrator import OrchestratorAgent

logger = logging.getLogger("shangtanai.pipeline")
router = APIRouter()


class PipelineCreateRequest(BaseModel):
    keyword: str
    platforms: list[str] = ["douyin", "taobao"]
    name: str | None = None
    config: dict = {}


class StepApproveRequest(BaseModel):
    edits: dict | None = None


# ── Helpers ──

def _pipeline_to_dict(p: Pipeline) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "keyword": p.trigger_keyword,
        "platforms": p.target_platforms,
        "status": p.status.value,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "steps": [
            {
                "id": s.id,
                "type": s.step_type.value,
                "order": s.step_order,
                "status": s.status.value,
                "output_data": s.output_data,
                "error_message": s.error_message,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in sorted(p.steps, key=lambda s: s.step_order)
        ],
    }


# Default pipeline steps
DEFAULT_STEPS = [
    (StepType.scout, 1),
    (StepType.product_selection, 2),
    (StepType.content, 3),
    (StepType.publish_schedule, 4),
]


# ── Endpoints ──

@router.post("/create")
async def create_pipeline(
    req: PipelineCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pipeline with default steps."""
    pipeline = Pipeline(
        user_id=user.id,
        name=req.name or f"{req.keyword} 全链路分析",
        trigger_keyword=req.keyword,
        target_platforms=req.platforms,
        config=req.config,
        status=PipelineStatus.draft,
    )
    db.add(pipeline)
    await db.flush()

    for step_type, order in DEFAULT_STEPS:
        step = PipelineStep(
            pipeline_id=pipeline.id,
            step_type=step_type,
            step_order=order,
            status=StepStatus.pending,
        )
        db.add(step)

    await db.flush()

    # Reload with steps
    result = await db.execute(
        select(Pipeline).where(Pipeline.id == pipeline.id).options(selectinload(Pipeline.steps))
    )
    pipeline = result.scalar_one()

    return {
        "success": True,
        "data": _pipeline_to_dict(pipeline),
        "message": "流水线创建成功",
        "error": None,
    }


@router.post("/{pipeline_id}/run")
async def run_pipeline(
    pipeline_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start or resume pipeline execution in background."""
    result = await db.execute(select(Pipeline).where(
        Pipeline.id == pipeline_id, Pipeline.user_id == user.id
    ))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    if pipeline.status == PipelineStatus.running:
        raise HTTPException(status_code=400, detail="流水线正在执行中")

    # Run in background with a fresh session
    async def _run_in_background():
        async with async_session() as session:
            engine = OrchestratorAgent(session)
            try:
                await engine.run(pipeline_id)
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Pipeline {pipeline_id} background execution failed: {e}")

    background_tasks.add_task(_run_in_background)

    return {
        "success": True,
        "data": {"pipeline_id": pipeline_id},
        "message": "流水线已开始执行",
        "error": None,
    }


@router.get("/{pipeline_id}/status")
async def get_pipeline_status(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current pipeline status with all step results."""
    result = await db.execute(
        select(Pipeline)
        .where(Pipeline.id == pipeline_id, Pipeline.user_id == user.id)
        .options(selectinload(Pipeline.steps))
    )
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="流水线不存在")

    return {
        "success": True,
        "data": _pipeline_to_dict(pipeline),
        "message": "ok",
        "error": None,
    }


@router.get("/{pipeline_id}/stream")
async def pipeline_stream(
    pipeline_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint for real-time pipeline progress."""
    # Verify ownership
    result = await db.execute(select(Pipeline).where(
        Pipeline.id == pipeline_id, Pipeline.user_id == user.id
    ))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="流水线不存在")

    async def event_generator():
        while True:
            async with async_session() as session:
                result = await session.execute(
                    select(Pipeline)
                    .where(Pipeline.id == pipeline_id)
                    .options(selectinload(Pipeline.steps))
                )
                pipeline = result.scalar_one_or_none()
                if not pipeline:
                    break

                data = _pipeline_to_dict(pipeline)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                if pipeline.status.value in ("completed", "failed", "paused"):
                    break

            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{pipeline_id}/step/{step_id}/approve")
async def approve_step(
    pipeline_id: str,
    step_id: str,
    req: StepApproveRequest = StepApproveRequest(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a step and resume pipeline."""
    # Verify ownership
    result = await db.execute(select(Pipeline).where(
        Pipeline.id == pipeline_id, Pipeline.user_id == user.id
    ))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="流水线不存在")

    engine = OrchestratorAgent(db)
    try:
        await engine.approve_step(pipeline_id, step_id, edits=req.edits)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "data": {"pipeline_id": pipeline_id, "step_id": step_id},
        "message": "审批通过，流水线继续执行",
        "error": None,
    }


@router.patch("/{pipeline_id}/step/{step_id}/retry")
async def retry_step(
    pipeline_id: str,
    step_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retry a failed step."""
    result = await db.execute(select(Pipeline).where(
        Pipeline.id == pipeline_id, Pipeline.user_id == user.id
    ))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="流水线不存在")

    engine = OrchestratorAgent(db)
    try:
        await engine.retry_step(pipeline_id, step_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "data": {"pipeline_id": pipeline_id, "step_id": step_id},
        "message": "正在重试",
        "error": None,
    }


@router.get("/list")
async def list_pipelines(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's pipelines."""
    result = await db.execute(
        select(Pipeline)
        .where(Pipeline.user_id == user.id)
        .options(selectinload(Pipeline.steps))
        .order_by(Pipeline.created_at.desc())
        .limit(50)
    )
    pipelines = result.scalars().all()

    return {
        "success": True,
        "data": [_pipeline_to_dict(p) for p in pipelines],
        "message": "ok",
        "error": None,
    }
