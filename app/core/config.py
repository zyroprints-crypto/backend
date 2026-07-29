"""
Central application configuration.
All values are sourced from environment variables (.env in dev, real
env vars / secrets manager in prod). Nothing sensitive is hardcoded.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- App ----
    PROJECT_NAME: str = "Zyro Prints"
    ENV: str = Field(default="development")  # development | staging | production
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # ---- Security / JWT ----
    SECRET_KEY: str = Field(..., description="Used to sign access tokens")
    REFRESH_SECRET_KEY: str = Field(..., description="Used to sign refresh tokens")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OTP_EXPIRE_MINUTES: int = 5
    OTP_LENGTH: int = 6

    # ---- Database ----
    DATABASE_URL: str = Field(..., description="postgresql+psycopg://user:pass@host:5432/db")
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # ---- Redis ----
    REDIS_URL: str = "redis://redis:6379/0"

    # ---- Celery ----
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # ---- Object storage (S3-compatible) ----
    S3_ENDPOINT_URL: str = "https://s3.amazonaws.com"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "zyro-prints"
    S3_REGION: str = "ap-south-1"
    S3_USE_SSL: bool = True
    MAX_UPLOAD_SIZE_MB: int = 50
    # Same rationale as BACKEND_CORS_ORIGINS above — stored raw, parsed via property.
    ALLOWED_UPLOAD_EXTENSIONS_RAW: str = ".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.webp"

    @property
    def allowed_upload_extensions(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_UPLOAD_EXTENSIONS_RAW.split(",") if ext.strip()]

    # ---- CORS ----
    # Stored as a raw string and parsed via `cors_origins` below, because
    # pydantic-settings attempts to JSON-decode List[str] env vars *before*
    # any field_validator runs — which breaks plain comma-separated values
    # like "http://localhost:3000,http://localhost:5173".
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        raw = self.BACKEND_CORS_ORIGINS.strip()
        if raw.startswith("["):
            import json
            return json.loads(raw)
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    # ---- Rate limiting ----
    RATE_LIMIT_PER_MINUTE: int = 60

    # ---- Payments ----
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    STRIPE_SECRET_KEY: str = ""
    PHONEPE_MERCHANT_ID: str = ""

    # ---- Notifications ----
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMS_PROVIDER_API_KEY: str = ""
    FCM_SERVER_KEY: str = ""

    # ---- AI ----
    AI_PROVIDER_API_KEY: str = ""
    AI_PROVIDER_MODEL: str = "claude-sonnet-4-6"

    # ---- Firebase (Google Sign-In token verification) ----
    # This is the Firebase *project ID* only — a public identifier, not a
    # secret. Verification happens against Google's public keys via the
    # google-auth library, so no service-account credentials are needed.
    FIREBASE_PROJECT_ID: str = ""

    # ---- Platform business rules ----
    PLATFORM_COMMISSION_PERCENT: float = 12.0
    DEFAULT_DELIVERY_RADIUS_KM: float = 8.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
