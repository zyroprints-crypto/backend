from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.users.models import Address, User
from app.modules.users.repository import AddressRepository, UserRepository
from app.modules.users.schemas import AddressCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.addresses = AddressRepository(db)

    def get_profile(self, user_id: UUID) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def update_profile(self, user_id: UUID, payload: UserUpdate) -> User:
        user = self.get_profile(user_id)
        data = payload.model_dump(exclude_unset=True)
        return self.users.update(user, **data)

    def add_address(self, user_id: UUID, payload: AddressCreate) -> Address:
        if payload.is_default:
            for addr in self.addresses.list(limit=100, user_id=user_id):
                if addr.is_default:
                    self.addresses.update(addr, is_default=False)
        address = Address(user_id=user_id, **payload.model_dump())
        return self.addresses.create(address)

    def list_addresses(self, user_id: UUID) -> list[Address]:
        return self.addresses.list(limit=100, user_id=user_id)

    def delete_address(self, user_id: UUID, address_id: UUID) -> None:
        address = self.addresses.get(address_id)
        if not address or address.user_id != user_id:
            raise NotFoundError("Address not found")
        self.addresses.soft_delete(address)
