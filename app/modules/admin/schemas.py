from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CouponCreate(BaseModel):
    code: str
    vendor_id: UUID | None = None
    discount_percent: float
    max_discount_amount: int | None = None
    min_order_amount: int = 0
    max_uses: int | None = None


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    vendor_id: UUID | None
    discount_percent: float
    max_discount_amount: int | None
    min_order_amount: int
    max_uses: int | None
    used_count: int
    is_active: bool


class PlatformSettingUpdate(BaseModel):
    value: str


class PlatformSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key: str
    value: str
    description: str | None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None
    action: str
    target_type: str | None
    target_id: str | None
    details: str | None
