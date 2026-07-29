"""
Auth service: registration, password login, OTP login/verification,
token refresh, forgot/reset password, and Google Sign-In (verifies the
Firebase ID token, then finds-or-creates a user).
"""
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AlreadyExistsError, NotFoundError, UnauthorizedError, ValidationAppError
from app.core.redis_client import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import TokenPair
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserOut, UserRegister

_google_request = google_requests.Request()


def _otp_key(phone: str) -> str:
    return f"otp:{phone}"


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def _issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_access_token(user.id, user.role.value),
            refresh_token=create_refresh_token(user.id),
            user=UserOut.model_validate(user),
        )

    def register(self, payload: UserRegister) -> TokenPair:
        if self.users.get_by_phone(payload.phone):
            raise AlreadyExistsError("An account with this phone number already exists")
        if payload.email and self.users.get_by_email(payload.email):
            raise AlreadyExistsError("An account with this email already exists")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            hashed_password=hash_password(payload.password),
            role=payload.role,
        )
        user = self.users.create(user)
        return self._issue_tokens(user)

    def login_with_password(self, phone: str, password: str) -> TokenPair:
        user = self.users.get_by_phone(phone)
        if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid phone number or password")
        if not user.is_active:
            raise UnauthorizedError("Account disabled")
        return self._issue_tokens(user)

    def request_otp(self, phone: str) -> None:
        otp = generate_otp()
        redis_client.setex(_otp_key(phone), settings.OTP_EXPIRE_MINUTES * 60, otp)
        # In production this dispatches an async Celery task via the SMS provider.
        # e.g. send_otp_sms.delay(phone, otp)

    def verify_otp_and_login(self, phone: str, otp: str) -> TokenPair:
        stored = redis_client.get(_otp_key(phone))
        if not stored or stored != otp:
            raise ValidationAppError("Invalid or expired OTP")
        redis_client.delete(_otp_key(phone))

        user = self.users.get_by_phone(phone)
        if not user:
            # First-time OTP login auto-provisions a customer account.
            user = User(full_name="New User", phone=phone, is_phone_verified=True)
            user = self.users.create(user)
        elif not user.is_phone_verified:
            self.users.update(user, is_phone_verified=True)

        return self._issue_tokens(user)

    def forgot_password(self, phone: str) -> None:
        if not self.users.get_by_phone(phone):
            raise NotFoundError("No account with this phone number")
        self.request_otp(phone)

    def reset_password(self, phone: str, otp: str, new_password: str) -> None:
        stored = redis_client.get(_otp_key(phone))
        if not stored or stored != otp:
            raise ValidationAppError("Invalid or expired OTP")
        user = self.users.get_by_phone(phone)
        if not user:
            raise NotFoundError("User not found")
        redis_client.delete(_otp_key(phone))
        self.users.update(user, hashed_password=hash_password(new_password))

    def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, token_type="refresh")
        except ValueError as exc:
            raise UnauthorizedError(str(exc)) from exc
        user = self.users.get(payload["sub"])
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")
        return self._issue_tokens(user)

    def google_login(self, id_token: str) -> TokenPair:
        """
        Verifies a Firebase ID token against Google's public keys (no service
        account credentials needed — just the project ID as the expected
        audience), then finds an existing user by email or provisions a new
        customer account, and issues our own JWT pair either way. The rest of
        the app never sees or trusts Firebase tokens beyond this one call.
        """
        if not settings.FIREBASE_PROJECT_ID:
            raise ValidationAppError("Google Sign-In is not configured on this server")

        try:
            claims = google_id_token.verify_firebase_token(
                id_token, _google_request, audience=settings.FIREBASE_PROJECT_ID
            )
        except ValueError as exc:
            raise UnauthorizedError("Invalid or expired Google sign-in token") from exc

        google_uid = claims.get("sub") or claims.get("user_id")
        email = claims.get("email")
        full_name = claims.get("name") or (email.split("@")[0] if email else "Google User")
        avatar_url = claims.get("picture")

        if not google_uid:
            raise ValidationAppError("Google token did not include a user id")

        user = self.users.get_by_google_id(google_uid)
        if not user and email:
            # Link an existing password/OTP account with the same verified email.
            user = self.users.get_by_email(email)
            if user:
                self.users.update(user, google_id=google_uid)

        if not user:
            if email and self.users.get_by_email(email):
                raise AlreadyExistsError("An account with this email already exists")
            user = self.users.create(User(
                full_name=full_name, email=email, google_id=google_uid,
                is_email_verified=bool(email), avatar_url=avatar_url,
            ))

        if not user.is_active:
            raise UnauthorizedError("Account disabled")

        return self._issue_tokens(user)
