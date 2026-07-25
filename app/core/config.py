"""
Central application configuration.
Environment variables are loaded from .env in development
and Render environment variables in production.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ---- App ----
    PROJECT_NAME: str = "Zyro Prints"
    ENV: str = "production"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False


    # ---- Security / JWT ----
    SECRET_KEY: str = "change_this_secret_key"
    REFRESH_SECRET_KEY: str = "change_this_refresh_secret_key"

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    OTP_EXPIRE_MINUTES: int = 5
    OTP_LENGTH: int = 6


    # ---- Database ----
    DATABASE_URL: str = ""

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False


    # ---- Redis ----
    REDIS_URL: str = "redis://redis:6379/0"


    # ---- Celery ----
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"


    # ---- Storage ----
    S3_ENDPOINT_URL: str = "https://s3.amazonaws.com"

    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    S3_BUCKET_NAME: str = "zyro-prints"
    S3_REGION: str = "ap-south-1"

    S3_USE_SSL: bool = True

    MAX_UPLOAD_SIZE_MB: int = 50

    ALLOWED_UPLOAD_EXTENSIONS_RAW: str = (
        ".pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.webp"
    )


    @property
    def allowed_upload_extensions(self) -> List[str]:
        return [
            ext.strip()
            for ext in self.ALLOWED_UPLOAD_EXTENSIONS_RAW.split(",")
            if ext.strip()
        ]


    # ---- CORS ----
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"


    @property
    def cors_origins(self) -> List[str]:
        raw = self.BACKEND_CORS_ORIGINS.strip()

        if raw.startswith("["):
            import json
            return json.loads(raw)

        return [
            origin.strip()
            for origin in raw.split(",")
            if origin.strip()
        ]


    # ---- Rate Limit ----
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


    # ---- Business Rules ----
    PLATFORM_COMMISSION_PERCENT: float = 12.0
    DEFAULT_DELIVERY_RADIUS_KM: float = 8.0



@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
