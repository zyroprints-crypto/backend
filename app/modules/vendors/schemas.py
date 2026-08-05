from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.vendors.models import VendorStatus


class VendorRegister(BaseModel):
    shop_name: str
    description: str | None = None
    gst_number: str | None = None
    address_line: str
    city: str
    state: str
    pincode: str
    latitude: float
    longitude: float
    phone: str
    email: str | None = None
    delivery_radius_km: float = 8.0


class VendorUpdate(BaseModel):
    shop_name: str | None = None
    description: str | None = None
    logo_url: str | None = None
    cover_image_url: str | None = None
    business_hours: dict | None = None
    social_links: dict | None = None
    delivery_radius_km: float | None = None
    phone: str | None = None
    email: str | None = None


class VendorBankDetails(BaseModel):
    bank_account_number: str
    bank_ifsc: str
    bank_account_holder: str


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    shop_name: str
    slug: str
    logo_url: str | None
    cover_image_url: str | None
    description: str | None
    city: str
    state: str
    latitude: float
    longitude: float
    delivery_radius_km: float
    status: VendorStatus
    is_verified: bool
    rating_avg: float
    rating_count: int


class VendorAdminAction(BaseModel):
    reason: str | None = None
