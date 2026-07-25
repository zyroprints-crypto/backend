"""
Shared mixins for every table:
- UUID primary key
- created_at / updated_at
- soft delete (is_deleted + deleted_at) instead of hard DELETE
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from app.common.db_types import GUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BaseEntity(UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    """Inherit from this (plus Base) for almost every domain table."""
    __abstract__ = True
