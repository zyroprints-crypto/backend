from pydantic import BaseModel, Field

from app.modules.users.schemas import UserOut


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    phone: str
    password: str


class OTPRequest(BaseModel):
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")


class OTPVerify(BaseModel):
    phone: str
    otp: str


class ForgotPasswordRequest(BaseModel):
    phone: str


class ResetPasswordRequest(BaseModel):
    phone: str
    otp: str
    new_password: str = Field(min_length=8, max_length=100)


class GoogleLoginRequest(BaseModel):
    id_token: str
