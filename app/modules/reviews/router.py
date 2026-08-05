from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_vendor
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.reviews.schemas import ReviewCreate, ReviewOut, ReviewReply
from app.modules.reviews.service import ReviewService
from app.modules.users.models import User

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=SuccessResponse[ReviewOut], status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    review = ReviewService(db).create_review(current_user.id, payload)
    return SuccessResponse(message="Review submitted", data=ReviewOut.model_validate(review))


@router.get("/vendor/{vendor_id}", response_model=SuccessResponse[list[ReviewOut]])
def vendor_reviews(vendor_id: UUID, db: Session = Depends(get_db)):
    reviews = ReviewService(db).list_for_vendor(vendor_id)
    return SuccessResponse(data=[ReviewOut.model_validate(r) for r in reviews])


@router.patch("/{review_id}/reply", response_model=SuccessResponse[ReviewOut])
def reply_to_review(
    review_id: UUID, payload: ReviewReply, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)
):
    review = ReviewService(db).reply(current_user.id, review_id, payload.vendor_reply)
    return SuccessResponse(message="Reply posted", data=ReviewOut.model_validate(review))
