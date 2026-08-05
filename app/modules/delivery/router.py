from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.delivery.schemas import DeliveryLocationUpdate, DeliveryTaskOut
from app.modules.delivery.service import DeliveryService
from app.modules.users.models import User

router = APIRouter(prefix="/delivery", tags=["Delivery"])


@router.get("/order/{order_id}", response_model=SuccessResponse[DeliveryTaskOut])
def track_order(order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = DeliveryService(db).get_for_order(order_id)
    return SuccessResponse(data=DeliveryTaskOut.model_validate(task))


@router.patch("/tasks/{task_id}/location", response_model=SuccessResponse[DeliveryTaskOut])
def update_location(
    task_id: UUID, payload: DeliveryLocationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    task = DeliveryService(db).update_location(current_user.id, task_id, payload)
    return SuccessResponse(message="Location updated", data=DeliveryTaskOut.model_validate(task))
