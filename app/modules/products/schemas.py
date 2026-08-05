from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductVariantCreate(BaseModel):
    sku: str
    attributes: dict = Field(default_factory=dict)
    price: int  # paise
    stock_qty: int = 0
    image_url: str | None = None


class ProductVariantOut(ProductVariantCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class ProductCreate(BaseModel):
    category_id: UUID
    title: str
    slug: str
    description: str | None = None
    images: list[str] = Field(default_factory=list)
    base_price: int
    customization_options: dict = Field(default_factory=dict)
    delivery_time_days: int = 3
    variants: list[ProductVariantCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    images: list[str] | None = None
    base_price: int | None = None
    customization_options: dict | None = None
    delivery_time_days: int | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    vendor_id: UUID
    category_id: UUID
    title: str
    slug: str
    description: str | None
    images: list[str]
    base_price: int
    customization_options: dict
    delivery_time_days: int
    is_active: bool
    rating_avg: float
    rating_count: int
    variants: list[ProductVariantOut] = Field(default_factory=list)
