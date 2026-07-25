from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.notifications.models import Notification, NotificationChannel
from app.modules.notifications.repository import NotificationRepository


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationRepository(db)

    def create(self, user_id: UUID, channel: NotificationChannel, title: str, body: str) -> Notification:
        notif = self.notifications.create(Notification(user_id=user_id, channel=channel, title=title, body=body))
        # Dispatch the actual delivery asynchronously.
        from app.modules.notifications.tasks import dispatch_notification
        dispatch_notification.delay(str(notif.id))
        return notif

    def list_for_user(self, user_id: UUID) -> list[Notification]:
        return self.notifications.list(limit=100, user_id=user_id)

    def mark_read(self, user_id: UUID, notification_id: UUID) -> Notification:
        notif = self.notifications.get(notification_id)
        if not notif:
            raise NotFoundError("Notification not found")
        if notif.user_id != user_id:
            raise ForbiddenError("Not your notification")
        return self.notifications.update(notif, is_read=True)
