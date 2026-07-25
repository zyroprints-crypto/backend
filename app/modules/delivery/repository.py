from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.delivery.models import DeliveryTask


class DeliveryTaskRepository(BaseRepository[DeliveryTask]):
    def __init__(self, db: Session):
        super().__init__(db, DeliveryTask)

    def get_by_order(self, order_id):
        stmt = select(DeliveryTask).where(DeliveryTask.order_id == order_id, DeliveryTask.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()
