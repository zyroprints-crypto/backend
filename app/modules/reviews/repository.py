from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.reviews.models import Review


class ReviewRepository(BaseRepository[Review]):
    def __init__(self, db: Session):
        super().__init__(db, Review)
