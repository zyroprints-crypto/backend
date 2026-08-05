import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class DeliveryStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"


class DeliveryTask(Base, BaseEntity):
    """
    Future-ready: tracks a delivery leg for an order, regardless of whether
    it's fulfilled by the vendor's own rider or (future) platform delivery partners.
    """
    __tablename__ = "delivery_tasks"

    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    delivery_partner_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus, name="delivery_status"), default=DeliveryStatus.ASSIGNED)
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    tracking_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
