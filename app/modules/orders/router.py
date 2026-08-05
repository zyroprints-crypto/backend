from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_vendor
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.orders.schemas import CheckoutRequest, OrderOut, OrderStatusUpdate
from app.modules.orders.service import OrderService
from app.modules.users.models import User

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/checkout", response_model=SuccessResponse[OrderOut], status_code=status.HTTP_201_CREATED)
def checkout(payload: CheckoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = OrderService(db).checkout(current_user.id, payload)
    return SuccessResponse(message="Order placed", data=OrderOut.model_validate(order))


@router.get("/me", response_model=SuccessResponse[list[OrderOut]])
def my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = OrderService(db).list_for_customer(current_user.id)
    return SuccessResponse(data=[OrderOut.model_validate(o) for o in orders])


@router.get("/vendor/incoming", response_model=SuccessResponse[list[OrderOut]])
def vendor_orders(current_user: User = Depends(require_vendor), db: Session = Depends(get_db)):
    orders = OrderService(db).list_for_vendor(current_user.id)
    return SuccessResponse(data=[OrderOut.model_validate(o) for o in orders])


@router.get("/{order_id}", response_model=SuccessResponse[OrderOut])
def get_order(order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = OrderService(db).get_order(order_id)
    return SuccessResponse(data=OrderOut.model_validate(order))


@router.patch("/{order_id}/status", response_model=SuccessResponse[OrderOut])
def update_order_status(
    order_id: UUID, payload: OrderStatusUpdate, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)
):
    order = OrderService(db).update_status(current_user.id, order_id, payload)
    return SuccessResponse(message="Order status updated", data=OrderOut.model_validate(order))


@router.post("/{order_id}/cancel", response_model=SuccessResponse[OrderOut])
def cancel_order(order_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = OrderService(db).cancel_order(current_user.id, order_id)
    return SuccessResponse(message="Order cancelled", data=OrderOut.model_validate(order))
