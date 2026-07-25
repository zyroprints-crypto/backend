import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class Coupon(Base, BaseEntity):
    """Platform-wide (vendor_id=None) or vendor-specific discount coupon."""
    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=True)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    max_discount_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)  # paise cap
    min_order_amount: Mapped[int] = mapped_column(Integer, default=0)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrderStatus(str, enum.Enum):
    PLACED = "placed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PRINTING = "printing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DeliveryMode(str, enum.Enum):
    VENDOR_DELIVERY = "vendor_delivery"
    CUSTOMER_PICKUP = "customer_pickup"
    PLATFORM_DELIVERY = "platform_delivery"


class Order(Base, BaseEntity):
    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=False)
    delivery_address_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("addresses.id"), nullable=True
    )

    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), default=OrderStatus.PLACED)
    delivery_mode: Mapped[DeliveryMode] = mapped_column(
        Enum(DeliveryMode, name="delivery_mode"), default=DeliveryMode.VENDOR_DELIVERY
    )

    subtotal: Mapped[int] = mapped_column(Integer, default=0)  # paise
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    delivery_fee: Mapped[int] = mapped_column(Integer, default=0)
    platform_commission: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[int] = mapped_column(Integer, default=0)

    coupon_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("payments.id", use_alter=True, name="fk_orders_payment_id"), nullable=True
    )

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusEvent"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base, BaseEntity):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id"), nullable=True
    )
    print_document_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("print_documents.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # paise, snapshot at order time
    line_total: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")


class OrderStatusEvent(Base, BaseEntity):
    """Immutable audit trail of every status transition for an order."""
    __tablename__ = "order_status_events"

    order_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status_event_status"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="status_history")
