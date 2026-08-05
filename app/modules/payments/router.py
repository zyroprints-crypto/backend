from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.payments.schemas import InitiatePaymentRequest
from app.modules.payments.service import PaymentService
from app.modules.users.models import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
def initiate_payment(
    payload: InitiatePaymentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    result = PaymentService(db).initiate(current_user.id, payload)
    return SuccessResponse(message="Payment initiated", data=result)
