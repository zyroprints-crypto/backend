"""
Abstract file-storage interface with an S3-compatible implementation (works
with AWS S3, MinIO, DigitalOcean Spaces, Cloudflare R2, etc via boto3).
Swap StorageBackend for a different implementation without touching callers.
"""
from abc import ABC, abstractmethod
from typing import BinaryIO

import boto3
from botocore.client import Config

from app.core.config import settings
from app.core.exceptions import ValidationAppError


class StorageBackend(ABC):
    @abstractmethod
    def upload(self, file_obj: BinaryIO, key: str, content_type: str) -> str:
        """Uploads a file and returns its publicly retrievable (or signed) URL."""

    @abstractmethod
    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...


class S3StorageBackend(StorageBackend):
    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
            use_ssl=settings.S3_USE_SSL,
        )
        self._bucket = settings.S3_BUCKET_NAME

    def upload(self, file_obj: BinaryIO, key: str, content_type: str) -> str:
        self._client.upload_fileobj(file_obj, self._bucket, key, ExtraArgs={"ContentType": content_type})
        return f"{settings.S3_ENDPOINT_URL}/{self._bucket}/{key}"

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=expires_in
        )

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)


def validate_upload(filename: str, size_bytes: int) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_upload_extensions:
        raise ValidationAppError(f"File type '{ext}' is not allowed")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationAppError(f"File exceeds max upload size of {settings.MAX_UPLOAD_SIZE_MB}MB")


def get_storage_backend() -> StorageBackend:
    return S3StorageBackend()
