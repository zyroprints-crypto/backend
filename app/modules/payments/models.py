import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class PaymentProvider(str, enum.Enum):
    RAZORPAY = "razorpay"
    PHONEPE = "phonepe"
    STRIPE = "stripe"
    COD = "cod"
    WALLET = "wallet"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(Base, BaseEntity):
    __tablename__ = "payments"

    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=True)
    provider: Mapped[PaymentProvider] = mapped_column(Enum(PaymentProvider, name="payment_provider"), nullable=False)
    provider_reference_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.PENDING)


class VendorSettlement(Base, BaseEntity):
    """Batch payout record: platform pays a vendor for a period's completed orders."""
    __tablename__ = "vendor_settlements"

    vendor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processing, paid, failed
    reference_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
