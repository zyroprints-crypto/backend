from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.notifications.models import NotificationChannel


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    channel: NotificationChannel
    title: str
    body: str
    is_read: bool
