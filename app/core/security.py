"""
Password hashing + JWT (access & refresh) token creation/verification.
"""
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, secret: str, expires_delta: timedelta, extra_claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {"sub": subject, "iat": now, "exp": now + expires_delta}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID, role: str) -> str:
    return _create_token(
        subject=str(user_id),
        secret=settings.SECRET_KEY,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role, "type": "access"},
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        subject=str(user_id),
        secret=settings.REFRESH_SECRET_KEY,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra_claims={"type": "refresh"},
    )


def decode_token(token: str, token_type: Literal["access", "refresh"] = "access") -> dict:
    secret = settings.SECRET_KEY if token_type == "access" else settings.REFRESH_SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    if payload.get("type") != token_type:
        raise ValueError("Incorrect token type")
    return payload


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=settings.OTP_LENGTH))
