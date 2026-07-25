"""Celery tasks for order lifecycle events: nearby-vendor broadcast, GST invoice generation."""
import logging

from app.core.celery_app import celery_app

logger = logging.getLogger("zyro.orders")


@celery_app.task(name="orders.notify_nearby_vendors")
def notify_nearby_vendors(order_id: str) -> None:
    """Push the new order to nearby/eligible vendors (push notification + socket event)."""
    logger.info("Notifying vendors for order %s", order_id)


@celery_app.task(name="orders.generate_gst_invoice")
def generate_gst_invoice(order_id: str) -> None:
    """Render and store a GST-compliant PDF invoice for a completed order."""
    logger.info("Generating GST invoice for order %s", order_id)
