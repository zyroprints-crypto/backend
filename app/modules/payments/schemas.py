from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.payments.models import PaymentProvider, PaymentStatus


class InitiatePaymentRequest(BaseModel):
    order_id: UUID
    provider: PaymentProvider


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID | None
    provider: PaymentProvider
    amount: int
    status: PaymentStatus
    provider_reference_id: str | None
