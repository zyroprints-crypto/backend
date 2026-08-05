from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.models import DeliveryMode, OrderStatus


class CheckoutRequest(BaseModel):
    vendor_id: UUID
    delivery_address_id: UUID | None = None
    delivery_mode: DeliveryMode = DeliveryMode.VENDOR_DELIVERY
    coupon_code: str | None = None
    cart_item_ids: list[UUID] = Field(default_factory=list, description="Subset of cart items to check out; empty = all")


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_variant_id: UUID | None
    print_document_id: UUID | None
    quantity: int
    unit_price: int
    line_total: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_number: str
    customer_id: UUID
    vendor_id: UUID
    status: OrderStatus
    delivery_mode: DeliveryMode
    subtotal: int
    discount_amount: int
    delivery_fee: int
    platform_commission: int
    total_amount: int
    coupon_code: str | None
    items: list[OrderItemOut] = Field(default_factory=list)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = None


class OrderRatingRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    review_text: str | None = None
