from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.reviews.models import Review
from app.modules.reviews.repository import ReviewRepository
from app.modules.reviews.schemas import ReviewCreate
from app.modules.vendors.repository import VendorRepository


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.reviews = ReviewRepository(db)
        self.vendors = VendorRepository(db)

    def create_review(self, customer_id: UUID, payload: ReviewCreate) -> Review:
        review = self.reviews.create(Review(customer_id=customer_id, **payload.model_dump()))
        self._recompute_vendor_rating(payload.vendor_id)
        return review

    def reply(self, owner_id: UUID, review_id: UUID, reply_text: str) -> Review:
        review = self.reviews.get(review_id)
        if not review:
            raise NotFoundError("Review not found")
        vendor = self.vendors.get_by_owner(owner_id)
        if not vendor or vendor.id != review.vendor_id:
            raise ForbiddenError("You cannot reply to this review")
        return self.reviews.update(review, vendor_reply=reply_text)

    def list_for_vendor(self, vendor_id: UUID) -> list[Review]:
        return self.reviews.list(limit=200, vendor_id=vendor_id)

    def _recompute_vendor_rating(self, vendor_id: UUID) -> None:
        reviews = self.list_for_vendor(vendor_id)
        if not reviews:
            return
        avg = sum(r.rating for r in reviews) / len(reviews)
        vendor = self.vendors.get(vendor_id)
        self.vendors.update(vendor, rating_avg=round(avg, 2), rating_count=len(reviews))
