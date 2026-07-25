from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.users.models import Address, User


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone, User.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()


class AddressRepository(BaseRepository[Address]):
    def __init__(self, db: Session):
        super().__init__(db, Address)
