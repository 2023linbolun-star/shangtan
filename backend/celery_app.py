"""
Celery application for 商探AI background task processing.
Three queues: agents (AI pipelines), platform_io (API calls), fast (notifications).
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import REDIS_URL

app = Celery(
    "shangtanai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.discovery",
        "app.tasks.publishing",
        "app.tasks.monitoring",
        "app.tasks.learning",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="agents",
    task_queues={
        "agents": {"exchange": "agents", "routing_key": "agents"},
        "platform_io": {"exchange": "platform_io", "routing_key": "platform_io"},
        "fast": {"exchange": "fast", "routing_key": "fast"},
    },
    # Celery Beat schedule for autonomous operations
    beat_schedule={
        # Trend discovery: every 4 hours
        "discovery-loop": {
            "task": "app.tasks.discovery.trigger_discovery",
            "schedule": crontab(minute=0, hour="*/4"),
        },
        # Content publishing: check scheduled posts every 5 minutes
        "publish-scheduler": {
            "task": "app.tasks.publishing.check_scheduled_publishes",
            "schedule": crontab(minute="*/5"),
        },
        # Order/inventory monitoring: every 30 minutes
        "monitoring-loop": {
            "task": "app.tasks.monitoring.check_orders_and_inventory",
            "schedule": crontab(minute="*/30"),
        },
        # Platform token refresh: every hour
        "token-refresh": {
            "task": "app.tasks.monitoring.refresh_expiring_tokens",
            "schedule": crontab(minute=15),
        },
        # Sales data sync: every hour
        "sales-sync": {
            "task": "app.tasks.monitoring.sync_sales_data",
            "schedule": crontab(minute=30),
        },
        # Daily decision learning: 3am UTC
        "learning-digest": {
            "task": "app.tasks.learning.run_decision_learning",
            "schedule": crontab(minute=0, hour=3),
        },
        # Daily report: 7am UTC (3pm Beijing)
        "daily-report": {
            "task": "app.tasks.learning.generate_daily_reports",
            "schedule": crontab(minute=0, hour=7),
        },
    },
)
