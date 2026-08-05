from uuid import UUID

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    type: str  # "vendor" | "product"
    id: UUID
    title: str
    subtitle: str | None = None
    rating: float | None = None
    price: int | None = None
    image_url: str | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
