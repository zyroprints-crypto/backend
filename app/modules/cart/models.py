import uuid

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class CartItem(Base, BaseEntity):
    """
    A cart line can hold EITHER a product variant OR a priced print document
    (exactly one of the two foreign keys is set), so the same cart/checkout
    flow works for custom products and document printing alike.
    """
    __tablename__ = "cart_items"

    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    product_variant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("product_variants.id"), nullable=True
    )
    print_document_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("print_documents.id"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)


class WishlistItem(Base, BaseEntity):
    __tablename__ = "wishlist_items"

    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("products.id"), nullable=False)


class FavoriteShop(Base, BaseEntity):
    __tablename__ = "favorite_shops"

    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("vendors.id"), nullable=False)
