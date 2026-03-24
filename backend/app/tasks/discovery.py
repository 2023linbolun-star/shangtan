"""Discovery tasks — autonomous trend scanning and product evaluation."""
import logging
from celery_app import app

logger = logging.getLogger("shangtanai.tasks.discovery")


@app.task(queue="agents", soft_time_limit=300, time_limit=600)
def trigger_discovery():
    """Scan trends for all active stores with discovery schedules."""
    logger.info("Triggering discovery loop for all active stores")
    # TODO: Query active stores, spawn per-store discovery pipelines
    pass


@app.task(queue="agents", soft_time_limit=600, time_limit=900)
def run_discovery_pipeline(store_id: str, config: dict | None = None):
    """Run a full discovery pipeline for a single store."""
    logger.info("Running discovery pipeline for store %s", store_id)
    # TODO: TrendScanAgent -> EvaluationAgent -> SupplierAgent -> ContentAgent
    pass
