import enum
import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.db_types import GUID, PortableJSON

from app.common.base_model import BaseEntity
from app.core.database import Base


class VendorStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class Vendor(Base, BaseEntity):
    __tablename__ = "vendors"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), unique=True, nullable=False
    )
    shop_name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_line: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    business_hours: Mapped[dict] = mapped_column(PortableJSON, default=dict)  # {"mon": "9:00-21:00", ...}
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    social_links: Mapped[dict] = mapped_column(PortableJSON, default=dict)

    delivery_radius_km: Mapped[float] = mapped_column(Float, default=8.0)

    bank_account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_account_holder: Mapped[str | None] = mapped_column(String(150), nullable=True)

    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, name="vendor_status"), default=VendorStatus.PENDING, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(default=0)
    commission_percent: Mapped[float] = mapped_column(Float, default=12.0)
    wallet_balance: Mapped[float] = mapped_column(Float, default=0.0)

    owner: Mapped["User"] = relationship(back_populates="vendor_profile")  # noqa: F821
