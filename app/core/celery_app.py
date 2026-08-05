"""
Celery app used for async/background work:
- sending emails / SMS / push notifications
- AI document analysis
- generating GST invoices
- vendor payout settlement batches
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "zyro_prints",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.modules.notifications.tasks",
        "app.modules.documents.tasks",
        "app.modules.orders.tasks",
        "app.modules.payments.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
)
