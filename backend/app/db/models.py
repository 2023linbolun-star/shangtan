"""
SQLAlchemy models for 商探AI.
6 tables with jsonb for flexible schema.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Float, Integer, BigInteger, Text, DateTime, Enum, ForeignKey, Index,
    LargeBinary, UniqueConstraint, desc,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ──

class ProductStatus(str, enum.Enum):
    discovered = "discovered"
    selected = "selected"
    content_ready = "content_ready"
    listed = "listed"
    active = "active"
    archived = "archived"
    evaluated = "evaluated"
    sourced = "sourced"
    optimizing = "optimizing"
    declining = "declining"


class PipelineStatus(str, enum.Enum):
    draft = "draft"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"


class StepStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"
    awaiting_approval = "awaiting_approval"


class StepType(str, enum.Enum):
    scout = "scout"
    product_selection = "product_selection"
    content = "content"
    listing = "listing"
    publish_schedule = "publish_schedule"
    trend_scan = "trend_scan"
    supplier_match = "supplier_match"
    publish = "publish"
    ad_create = "ad_create"
    ad_optimize = "ad_optimize"
    price_optimize = "price_optimize"
    inventory_check = "inventory_check"
    order_monitor = "order_monitor"
    performance_review = "performance_review"


class ContentStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    published = "published"


# ── Models ──

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(50), default="新用户")
    credits: Mapped[int] = mapped_column(Integer, default=3000)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    pipelines: Mapped[list["Pipeline"]] = relationship(back_populates="user")
    products: Mapped[list["Product"]] = relationship(back_populates="user")
    stores: Mapped[list["Store"]] = relationship(back_populates="user")


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    trigger_keyword: Mapped[str] = mapped_column(String(100))
    target_platforms: Mapped[dict] = mapped_column(JSONB, default=list)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), index=True)
    template: Mapped[str | None] = mapped_column(String(50))
    schedule_id: Mapped[str | None] = mapped_column(String(36))
    is_autonomous: Mapped[bool] = mapped_column(default=False)
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus), default=PipelineStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    user: Mapped["User"] = relationship(back_populates="pipelines")
    store: Mapped["Store | None"] = relationship()
    steps: Mapped[list["PipelineStep"]] = relationship(
        back_populates="pipeline", order_by="PipelineStep.step_order"
    )
    products: Mapped[list["Product"]] = relationship(back_populates="pipeline")
    contents: Mapped[list["GeneratedContent"]] = relationship(back_populates="pipeline")


class PipelineStep(Base):
    __tablename__ = "pipeline_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pipeline_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipelines.id"), index=True)
    step_type: Mapped[StepType] = mapped_column(Enum(StepType))
    step_order: Mapped[int] = mapped_column(Integer)
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus), default=StepStatus.pending
    )
    input_data: Mapped[dict | None] = mapped_column(JSONB)
    output_data: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    pipeline: Mapped["Pipeline"] = relationship(back_populates="steps")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    pipeline_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pipelines.id"))
    keyword: Mapped[str] = mapped_column(String(100), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(500))
    price: Mapped[float] = mapped_column(Float)
    cost: Mapped[float | None] = mapped_column(Float)
    image_url: Mapped[str | None] = mapped_column(Text)
    scout_data: Mapped[dict | None] = mapped_column(JSONB)
    risk_tags: Mapped[dict | None] = mapped_column(JSONB, default=list)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"), index=True)
    supplier_url: Mapped[str | None] = mapped_column(String(500))
    supplier_cost: Mapped[float | None] = mapped_column(Float)
    supplier_name: Mapped[str | None] = mapped_column(String(200))
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_sale_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    lifecycle_stage: Mapped[str] = mapped_column(String(20), default="discovered")
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), default=ProductStatus.discovered
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="products")
    pipeline: Mapped["Pipeline | None"] = relationship(back_populates="products")
    contents: Mapped[list["GeneratedContent"]] = relationship(back_populates="product")

    __table_args__ = (
        Index("ix_products_user_status", "user_id", "status"),
    )


class GeneratedContent(Base):
    __tablename__ = "generated_contents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    pipeline_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pipelines.id"))
    content_type: Mapped[str] = mapped_column(String(50))  # video_script, xhs_note, listing, etc.
    platform: Mapped[str] = mapped_column(String(20))
    content: Mapped[dict] = mapped_column(JSONB)
    ai_model: Mapped[str] = mapped_column(String(50))
    credits_used: Mapped[int] = mapped_column(Integer, default=0)
    feedback: Mapped[int | None] = mapped_column(Integer)  # 1=thumbs up, -1=thumbs down
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.draft
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    product: Mapped["Product"] = relationship(back_populates="contents")
    pipeline: Mapped["Pipeline | None"] = relationship(back_populates="contents")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)  # positive=credit, negative=debit
    operation: Mapped[str] = mapped_column(String(50))  # register_bonus, ai_call, checkin, etc.
    pipeline_id: Mapped[str | None] = mapped_column(String(36))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ── Agent 进化系统 ──

class AgentMemory(Base):
    """每次 Agent 执行的记录，用于学习和进化。"""
    __tablename__ = "agent_memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    agent_type: Mapped[str] = mapped_column(String(50), index=True)

    task_input_hash: Mapped[str] = mapped_column(String(20), default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    duration_ms: Mapped[float] = mapped_column(Float, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    ai_calls: Mapped[dict | None] = mapped_column(JSONB, default=list)

    # 用户反馈（后续填入）
    feedback_score: Mapped[int | None] = mapped_column(Integer)  # -1, 0, 1
    edit_distance: Mapped[float | None] = mapped_column(Float)  # 0.0-1.0
    was_rejected: Mapped[bool] = mapped_column(default=False)
    feedback_notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_agent_mem_user_type", "user_id", "agent_type"),
    )


class UserDNA(Base):
    """用户偏好画像，随交互逐步积累。"""
    __tablename__ = "user_dna"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True)

    store_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    content_preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    scout_preferences: Mapped[dict] = mapped_column(JSONB, default=dict)

    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    version: Mapped[int] = mapped_column(Integer, default=1)


class FewShotExample(Base):
    """用户认可的优秀输出，用于 few-shot 注入。"""
    __tablename__ = "few_shot_examples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    agent_type: Mapped[str] = mapped_column(String(50), index=True)

    keyword: Mapped[str] = mapped_column(String(100), default="")
    platform: Mapped[str | None] = mapped_column(String(20))
    output_summary: Mapped[str] = mapped_column(Text, default="")
    feedback_score: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_fewshot_user_type", "user_id", "agent_type"),
    )


class FailurePattern(Base):
    """Agent 的失败模式库，用于避免重复犯错。"""
    __tablename__ = "failure_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    agent_type: Mapped[str] = mapped_column(String(50), index=True)

    pattern_description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="user_rejection")
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_failure_user_type", "user_id", "agent_type"),
    )


# ── v2.0 新增模型 ──

class Store(Base):
    """Multi-store management — 多店铺管理。"""
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    platform: Mapped[str] = mapped_column(String(20))
    store_url: Mapped[str | None] = mapped_column(String(500))
    store_dna: Mapped[dict] = mapped_column(JSONB, default=dict)
    operation_mode: Mapped[str] = mapped_column(String(10), default="review")
    approval_gates: Mapped[dict] = mapped_column(JSONB, default=dict)
    risk_thresholds: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["User"] = relationship(back_populates="stores")
    credentials: Mapped[list["PlatformCredential"]] = relationship(back_populates="store")


class PlatformCredential(Base):
    """Encrypted per-store platform credentials — 加密平台凭证。"""
    __tablename__ = "platform_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), index=True)
    platform: Mapped[str] = mapped_column(String(20))
    credential_type: Mapped[str] = mapped_column(String(20))
    encrypted_data: Mapped[bytes] = mapped_column(LargeBinary)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    store: Mapped["Store"] = relationship(back_populates="credentials")

    __table_args__ = (
        UniqueConstraint("store_id", "platform", name="uq_credential_store_platform"),
    )


class PipelineSchedule(Base):
    """Autonomous scheduling — 自主调度计划。"""
    __tablename__ = "pipeline_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), index=True)
    pipeline_template: Mapped[str] = mapped_column(String(50))
    cron_expression: Mapped[str] = mapped_column(String(50))
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    enabled: Mapped[bool] = mapped_column(default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AIDecision(Base):
    """Decision audit log — AI决策审计日志。"""
    __tablename__ = "ai_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"))
    pipeline_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pipelines.id"))
    decision_type: Mapped[str] = mapped_column(String(50))
    input_summary: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[dict] = mapped_column(JSONB)
    reasoning: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    outcome: Mapped[dict | None] = mapped_column(JSONB)
    outcome_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_ai_decisions_store_type", "store_id", "decision_type"),
    )


class ManualTask(Base):
    """Tasks for platforms without API — 无API平台的手动任务。"""
    __tablename__ = "manual_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    store_id: Mapped[str] = mapped_column(String(36), ForeignKey("stores.id"), index=True)
    pipeline_step_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pipeline_steps.id"))
    task_type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str] = mapped_column(Text)
    copy_content: Mapped[dict | None] = mapped_column(JSONB)
    attachments: Mapped[dict] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class EventLog(Base):
    """Persistent event audit — 持久化事件审计日志。"""
    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    store_id: Mapped[str | None] = mapped_column(String(36))
    pipeline_id: Mapped[str | None] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_event_log_store_created", "store_id", desc("created_at")),
    )


class TrendSignal(Base):
    """Discovered trends — 发现的趋势信号。"""
    __tablename__ = "trend_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    store_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("stores.id"))
    keyword: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[str] = mapped_column(String(50))
    velocity_score: Mapped[float] = mapped_column(Float)
    volume_score: Mapped[float] = mapped_column(Float)
    competition_score: Mapped[float | None] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_trend_signals_status_score", "status", desc("overall_score")),
    )
