"""Publishing tasks — scheduled content distribution."""
import logging
from celery_app import app

logger = logging.getLogger("shangtanai.tasks.publishing")


@app.task(queue="platform_io", soft_time_limit=120, time_limit=180)
def check_scheduled_publishes():
    """Check for content scheduled to publish now, execute."""
    logger.info("Checking scheduled publishes")
    # TODO: Query content_schedules due now, publish via platform adapters
    pass


@app.task(queue="platform_io", soft_time_limit=60, time_limit=120)
def publish_to_platform(content_id: str, platform: str, store_id: str):
    """Publish a single piece of content to a platform."""
    logger.info("Publishing content %s to %s for store %s", content_id, platform, store_id)
    # TODO: Load content, get platform adapter, call publish
    pass
