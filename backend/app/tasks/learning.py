"""Learning tasks — decision feedback and report generation."""
import logging
from celery_app import app

logger = logging.getLogger("shangtanai.tasks.learning")


@app.task(queue="agents", soft_time_limit=300, time_limit=600)
def run_decision_learning():
    """Process outcomes of past AI decisions to improve future ones."""
    logger.info("Running decision learning digest")
    # TODO: Query decisions with new outcome data, update few-shot/failure patterns
    pass


@app.task(queue="agents", soft_time_limit=120, time_limit=180)
def generate_daily_reports():
    """Generate daily performance reports for all active stores."""
    logger.info("Generating daily reports")
    # TODO: For each store, aggregate metrics, generate AI summary, push notification
    pass
