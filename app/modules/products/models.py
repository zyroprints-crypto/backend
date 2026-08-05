import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.db_types import GUID, PortableJSON, PortableArray

from app.common.base_model import BaseEntity
from app.core.database import Base


class Product(Base, BaseEntity):
    """
    A custom-printing product listed by a vendor: mug, t-shirt, poster, sticker,
    business card, wedding invitation, etc. Actual buyable SKUs are ProductVariant rows.
    """
    __tablename__ = "products"

    vendor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("categories.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[list[str]] = mapped_column(PortableArray(String), default=list)

    base_price: Mapped[float] = mapped_column(Integer, nullable=False)  # in paise/cents for precision
    customization_options: Mapped[dict] = mapped_column(PortableJSON, default=dict)  # e.g. {"colors": [...], "sizes": [...]}
    delivery_time_days: Mapped[int] = mapped_column(Integer, default=3)

    is_active: Mapped[bool] = mapped_column(default=True)
    rating_avg: Mapped[float] = mapped_column(default=0.0)
    rating_count: Mapped[int] = mapped_column(default=0)

    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base, BaseEntity):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    attributes: Mapped[dict] = mapped_column(PortableJSON, default=dict)  # {"size": "L", "color": "Black"}
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # in paise
    stock_qty: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="variants")
