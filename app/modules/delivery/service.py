from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.delivery.models import DeliveryTask
from app.modules.delivery.repository import DeliveryTaskRepository
from app.modules.delivery.schemas import DeliveryLocationUpdate


class DeliveryService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = DeliveryTaskRepository(db)

    def get_for_order(self, order_id: UUID) -> DeliveryTask:
        task = self.tasks.get_by_order(order_id)
        if not task:
            raise NotFoundError("No delivery task for this order yet")
        return task

    def update_location(self, delivery_partner_id: UUID, task_id: UUID, payload: DeliveryLocationUpdate) -> DeliveryTask:
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError("Delivery task not found")
        if task.delivery_partner_id != delivery_partner_id:
            raise ForbiddenError("Not assigned to you")
        fields = {"current_latitude": payload.latitude, "current_longitude": payload.longitude}
        if payload.status:
            fields["status"] = payload.status
        return self.tasks.update(task, **fields)
