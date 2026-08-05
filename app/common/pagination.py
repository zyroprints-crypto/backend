"""Reusable pagination query params + response envelope."""
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def pagination_params(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> PageParams:
    return PageParams(page=page, page_size=page_size)


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def build(cls, items: List[T], total: int, params: PageParams) -> "Page[T]":
        total_pages = (total + params.page_size - 1) // params.page_size if params.page_size else 0
        return cls(items=items, total=total, page=params.page, page_size=params.page_size, total_pages=total_pages)
