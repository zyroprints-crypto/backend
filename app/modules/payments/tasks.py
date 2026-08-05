"""Celery tasks: batch vendor settlements, invoice PDF generation."""
import logging

from app.core.celery_app import celery_app

logger = logging.getLogger("zyro.payments")


@celery_app.task(name="payments.run_vendor_settlement_batch")
def run_vendor_settlement_batch() -> None:
    """Scheduled (e.g. weekly via Celery beat) payout run for all vendors with completed, unsettled orders."""
    logger.info("Running vendor settlement batch")
