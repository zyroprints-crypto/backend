from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.users.models import UserRole


class UserBase(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=100)
    role: UserRole = UserRole.CUSTOMER


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    role: UserRole
    is_active: bool
    is_phone_verified: bool
    is_email_verified: bool
    avatar_url: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    avatar_url: str | None = None


class AddressCreate(BaseModel):
    label: str = "Home"
    line1: str
    line2: str | None = None
    city: str
    state: str
    pincode: str = Field(pattern=r"^[0-9]{4,10}$")
    latitude: float | None = None
    longitude: float | None = None
    is_default: bool = False


class AddressOut(AddressCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
