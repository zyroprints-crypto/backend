from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.search.schemas import SearchResponse
from app.modules.search.service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=SuccessResponse[SearchResponse])
def search(
    q: str = Query(..., min_length=1),
    category_id: UUID | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    min_rating: float | None = None,
    city: str | None = None,
    db: Session = Depends(get_db),
):
    result = SearchService(db).search(q, category_id, min_price, max_price, min_rating, city)
    return SuccessResponse(data=result)
