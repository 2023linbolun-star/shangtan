"""Monitoring tasks — orders, inventory, token refresh, sales sync."""
import logging
from celery_app import app

logger = logging.getLogger("shangtanai.tasks.monitoring")


@app.task(queue="platform_io", soft_time_limit=120, time_limit=180)
def check_orders_and_inventory():
    """Check order status and inventory levels for all active stores."""
    logger.info("Checking orders and inventory")
    # TODO: For each store, pull orders, check fulfillment status
    pass


@app.task(queue="fast", soft_time_limit=60, time_limit=120)
def refresh_expiring_tokens():
    """Refresh OAuth tokens that are about to expire."""
    logger.info("Refreshing expiring platform tokens")
    # TODO: Query credentials expiring in <1 hour, refresh
    pass


@app.task(queue="platform_io", soft_time_limit=120, time_limit=180)
def sync_sales_data():
    """Pull sales data from all connected platforms."""
    logger.info("Syncing sales data")
    # TODO: For each store with credentials, pull sales from platform APIs
    pass
