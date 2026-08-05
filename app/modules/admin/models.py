import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class AuditLog(Base, BaseEntity):
    """Immutable record of sensitive admin/system actions for compliance and debugging."""
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(150), nullable=False)  # e.g. "vendor.approve"
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)


class PlatformSetting(Base, BaseEntity):
    """Key-value platform settings editable from the admin panel (commission %, feature flags, etc).
    Also backs: maintenance mode (key='maintenance_mode') and configurable
    pricing rules (key='pricing.<rate_name>') — see app/modules/admin/pricing_config.py.
    """
    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class City(Base, BaseEntity):
    """Managed list of cities the platform operates in (admin add/remove)."""
    __tablename__ = "cities"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)


class Banner(Base, BaseEntity):
    """Homepage promotional banners, admin-managed."""
    __tablename__ = "banners"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    link_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)


class ComplaintStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class Complaint(Base, BaseEntity):
    """Customer/vendor complaints escalated to platform admins."""
    __tablename__ = "complaints"

    raised_by_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status"), default=ComplaintStatus.OPEN
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class LoginEvent(Base, BaseEntity):
    """Every successful login, for the admin's 'every login' visibility requirement."""
    __tablename__ = "login_events"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)  # password | otp | google
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
