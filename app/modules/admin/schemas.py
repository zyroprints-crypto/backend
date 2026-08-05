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


# ---- Cities ----
class CityCreate(BaseModel):
    name: str
    state: str
    slug: str


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    state: str
    slug: str
    is_active: bool


# ---- Banners ----
class BannerCreate(BaseModel):
    title: str
    image_url: str
    link_url: str | None = None
    display_order: int = 0


class BannerUpdate(BaseModel):
    title: str | None = None
    image_url: str | None = None
    link_url: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class BannerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    image_url: str
    link_url: str | None
    display_order: int
    is_active: bool


# ---- Complaints ----
class ComplaintUpdate(BaseModel):
    status: str  # "open" | "in_progress" | "resolved" | "dismissed"
    resolution_note: str | None = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    raised_by_id: UUID
    order_id: UUID | None
    vendor_id: UUID | None
    subject: str
    description: str
    status: str
    resolution_note: str | None


# ---- Pricing rules ----
class PricingRatesOut(BaseModel):
    rates: dict[str, float]


class PricingRateUpdate(BaseModel):
    value: float


# ---- Vendor admin-management (create/edit/delete by admin, beyond approve/suspend) ----
class VendorAdminCreate(BaseModel):
    shop_name: str
    owner_email: str  # looked up or a new user is provisioned
    owner_full_name: str
    address_line: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    phone: str
    gst_number: str | None = None


class VendorAdminUpdate(BaseModel):
    shop_name: str | None = None
    address_line: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
    gst_number: str | None = None
    commission_percent: float | None = None


# ---- Maintenance mode ----
class MaintenanceModeOut(BaseModel):
    enabled: bool
    message: str | None = None


class MaintenanceModeUpdate(BaseModel):
    enabled: bool
    message: str | None = None


# ---- Refunds ----
class RefundRequest(BaseModel):
    reason: str | None = None


# ---- Login events ----
class LoginEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    method: str
    ip_address: str | None
