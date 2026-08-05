"""Standard success envelope so every endpoint returns a predictable shape."""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    details: Optional[Any] = None
