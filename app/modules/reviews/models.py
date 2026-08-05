import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class Review(Base, BaseEntity):
    __tablename__ = "reviews"

    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("orders.id"), nullable=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("products.id"), nullable=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
