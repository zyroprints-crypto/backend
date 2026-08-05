from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.schemas import AddressCreate, AddressOut, UserOut, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=SuccessResponse[UserOut])
def get_my_profile(current_user: User = Depends(get_current_user)):
    return SuccessResponse(data=UserOut.model_validate(current_user))


@router.patch("/me", response_model=SuccessResponse[UserOut])
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    updated = service.update_profile(current_user.id, payload)
    return SuccessResponse(message="Profile updated", data=UserOut.model_validate(updated))


@router.post("/me/addresses", response_model=SuccessResponse[AddressOut], status_code=status.HTTP_201_CREATED)
def add_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    address = service.add_address(current_user.id, payload)
    return SuccessResponse(message="Address added", data=AddressOut.model_validate(address))


@router.get("/me/addresses", response_model=SuccessResponse[list[AddressOut]])
def list_addresses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = UserService(db)
    addresses = service.list_addresses(current_user.id)
    return SuccessResponse(data=[AddressOut.model_validate(a) for a in addresses])


@router.delete("/me/addresses/{address_id}", response_model=SuccessResponse)
def delete_address(address_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = UserService(db)
    service.delete_address(current_user.id, address_id)
    return SuccessResponse(message="Address deleted")
