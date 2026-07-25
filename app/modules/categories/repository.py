from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.categories.models import Category


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)
