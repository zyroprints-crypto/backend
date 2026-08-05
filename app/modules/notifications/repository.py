from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.notifications.models import Notification


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: Session):
        super().__init__(db, Notification)
