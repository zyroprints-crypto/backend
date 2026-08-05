import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class Category(Base, BaseEntity):
    """
    Supports both document-printing categories (Business Card, Poster...) and
    custom-product categories (Mug, T-Shirt...) via self-referencing parent_id,
    e.g. 'Wedding Invitations' -> 'Royal Wedding' / 'Supreme Royal Wedding'.
    """
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("categories.id"), nullable=True)

    children: Mapped[list["Category"]] = relationship(back_populates="parent", cascade="all, delete-orphan")
    parent: Mapped["Category"] = relationship(back_populates="children", remote_side="Category.id")
