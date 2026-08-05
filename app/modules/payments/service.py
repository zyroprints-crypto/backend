from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.orders.repository import OrderRepository
from app.modules.payments.gateways import get_gateway
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import InitiatePaymentRequest


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.payments = PaymentRepository(db)
        self.orders = OrderRepository(db)

    def initiate(self, customer_id: UUID, payload: InitiatePaymentRequest) -> dict:
        order = self.orders.get(payload.order_id)
        if not order:
            raise NotFoundError("Order not found")

        payment = Payment(
            customer_id=customer_id, order_id=order.id, provider=payload.provider,
            amount=order.total_amount, status=PaymentStatus.PENDING,
        )
        payment = self.payments.create(payment)

        if payload.provider.value == "cod":
            self.payments.update(payment, status=PaymentStatus.SUCCESS)
            return {"payment_id": str(payment.id), "provider": "cod", "status": "success"}

        gateway = get_gateway(payload.provider.value)
        intent = gateway.create_payment_intent(order.total_amount, "INR", str(payment.id))
        return {"payment_id": str(payment.id), **intent}

    def mark_success(self, payment_id: UUID, provider_reference_id: str) -> Payment:
        payment = self.payments.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        return self.payments.update(payment, status=PaymentStatus.SUCCESS, provider_reference_id=provider_reference_id)

    def mark_failed(self, payment_id: UUID) -> Payment:
        payment = self.payments.get(payment_id)
        if not payment:
            raise NotFoundError("Payment not found")
        return self.payments.update(payment, status=PaymentStatus.FAILED)
