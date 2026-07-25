"""
Generic repository providing CRUD + soft-delete aware queries.
Concrete repositories subclass this and add domain-specific queries.
"""
from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id: UUID) -> ModelType | None:
        stmt = select(self.model).where(self.model.id == id, self.model.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, offset: int = 0, limit: int = 20, **filters) -> list[ModelType]:
        stmt = select(self.model).where(self.model.is_deleted.is_(False))
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self, **filters) -> int:
        stmt = select(self.model).where(self.model.is_deleted.is_(False))
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        return len(list(self.db.execute(stmt).scalars().all()))

    def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType, **fields) -> ModelType:
        for key, value in fields.items():
            setattr(obj, key, value)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def soft_delete(self, obj: ModelType) -> None:
        from datetime import datetime, timezone
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
