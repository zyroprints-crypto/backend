from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.notifications.schemas import NotificationOut
from app.modules.notifications.service import NotificationService
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=SuccessResponse[list[NotificationOut]])
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = NotificationService(db).list_for_user(current_user.id)
    return SuccessResponse(data=[NotificationOut.model_validate(i) for i in items])


@router.patch("/{notification_id}/read", response_model=SuccessResponse[NotificationOut])
def mark_read(notification_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = NotificationService(db).mark_read(current_user.id, notification_id)
    return SuccessResponse(data=NotificationOut.model_validate(notif))
