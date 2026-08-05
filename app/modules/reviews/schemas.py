from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    vendor_id: UUID
    order_id: UUID | None = None
    product_id: UUID | None = None
    rating: int = Field(ge=1, le=5)
    review_text: str | None = None


class ReviewReply(BaseModel):
    vendor_reply: str


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_id: UUID
    vendor_id: UUID
    order_id: UUID | None
    product_id: UUID | None
    rating: int
    review_text: str | None
    vendor_reply: str | None
