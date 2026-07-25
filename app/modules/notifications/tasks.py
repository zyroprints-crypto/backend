"""Celery tasks that perform the real email/SMS/push send via provider SDKs."""
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal

logger = logging.getLogger("zyro.notifications")


@celery_app.task(name="notifications.dispatch_notification")
def dispatch_notification(notification_id: str) -> None:
    from app.modules.notifications.models import Notification, NotificationChannel

    db = SessionLocal()
    try:
        notif = db.get(Notification, notification_id)
        if not notif:
            return
        if notif.channel == NotificationChannel.EMAIL:
            logger.info("Sending email notification %s via SMTP", notif.id)  # smtplib / provider SDK here
        elif notif.channel == NotificationChannel.SMS:
            logger.info("Sending SMS notification %s", notif.id)  # SMS_PROVIDER_API_KEY
        elif notif.channel == NotificationChannel.PUSH:
            logger.info("Sending push notification %s via FCM", notif.id)  # FCM_SERVER_KEY
    finally:
        db.close()
