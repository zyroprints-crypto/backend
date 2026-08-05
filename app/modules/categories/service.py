from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.categories.models import Category
from app.modules.categories.repository import CategoryRepository
from app.modules.categories.schemas import CategoryCreate


class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.categories = CategoryRepository(db)

    def create(self, payload: CategoryCreate) -> Category:
        return self.categories.create(Category(**payload.model_dump()))

    def list_all(self, offset: int = 0, limit: int = 100) -> list[Category]:
        return self.categories.list(offset=offset, limit=limit)

    def get(self, category_id: UUID) -> Category:
        category = self.categories.get(category_id)
        if not category:
            raise NotFoundError("Category not found")
        return category

    def delete(self, category_id: UUID) -> None:
        self.categories.soft_delete(self.get(category_id))
