from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class CartItemCreate(BaseModel):
    product_variant_id: UUID | None = None
    print_document_id: UUID | None = None
    quantity: int = 1

    @model_validator(mode="after")
    def exactly_one_reference(self):
        if bool(self.product_variant_id) == bool(self.print_document_id):
            raise ValueError("Provide exactly one of product_variant_id or print_document_id")
        return self


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_variant_id: UUID | None
    print_document_id: UUID | None
    quantity: int
    # Enrichment fields for display — populated by the service layer by
    # looking up the linked product variant / print document. Optional so
    # this stays backward compatible with any client built against the
    # bare linkage-only shape.
    title: str | None = None
    image_url: str | None = None
    unit_price: int | None = None


class WishlistCreate(BaseModel):
    product_id: UUID


class WishlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID


class FavoriteShopCreate(BaseModel):
    vendor_id: UUID


class FavoriteShopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    vendor_id: UUID
