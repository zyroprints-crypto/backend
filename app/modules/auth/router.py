from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    OTPRequest,
    OTPVerify,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserRegister

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=SuccessResponse[TokenPair], status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    tokens = AuthService(db).register(payload)
    return SuccessResponse(message="Registered successfully", data=tokens)


@router.post("/login", response_model=SuccessResponse[TokenPair])
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    tokens = AuthService(db).login_with_password(payload.phone, payload.password)
    return SuccessResponse(message="Logged in", data=tokens)


@router.post("/otp/request", response_model=SuccessResponse)
def request_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    AuthService(db).request_otp(payload.phone)
    return SuccessResponse(message="OTP sent")


@router.post("/otp/verify", response_model=SuccessResponse[TokenPair])
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    tokens = AuthService(db).verify_otp_and_login(payload.phone, payload.otp)
    return SuccessResponse(message="Logged in via OTP", data=tokens)


@router.post("/forgot-password", response_model=SuccessResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).forgot_password(payload.phone)
    return SuccessResponse(message="OTP sent to reset password")


@router.post("/reset-password", response_model=SuccessResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService(db).reset_password(payload.phone, payload.otp, payload.new_password)
    return SuccessResponse(message="Password reset successfully")


@router.post("/refresh", response_model=SuccessResponse[TokenPair])
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    tokens = AuthService(db).refresh(payload.refresh_token)
    return SuccessResponse(message="Token refreshed", data=tokens)
