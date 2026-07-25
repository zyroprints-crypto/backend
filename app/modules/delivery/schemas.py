from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.delivery.models import DeliveryStatus


class DeliveryLocationUpdate(BaseModel):
    latitude: float
    longitude: float
    status: DeliveryStatus | None = None


class DeliveryTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_id: UUID
    delivery_partner_id: UUID | None
    status: DeliveryStatus
    current_latitude: float | None
    current_longitude: float | None
