from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_admin, require_vendor
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.users.models import User
from app.modules.vendors.schemas import VendorBankDetails, VendorOut, VendorRegister, VendorUpdate
from app.modules.vendors.service import VendorService

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post("/register", response_model=SuccessResponse[VendorOut], status_code=status.HTTP_201_CREATED)
def register_vendor(
    payload: VendorRegister, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    vendor = VendorService(db).register_vendor(current_user.id, payload)
    return SuccessResponse(message="Vendor store submitted for approval", data=VendorOut.model_validate(vendor))


@router.get("/me/store", response_model=SuccessResponse[VendorOut])
def my_store(current_user: User = Depends(require_vendor), db: Session = Depends(get_db)):
    vendor = VendorService(db).get_my_store(current_user.id)
    return SuccessResponse(data=VendorOut.model_validate(vendor))


@router.patch("/me/store", response_model=SuccessResponse[VendorOut])
def update_my_store(
    payload: VendorUpdate, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)
):
    vendor = VendorService(db).update_store(current_user.id, payload)
    return SuccessResponse(message="Store updated", data=VendorOut.model_validate(vendor))


@router.put("/me/bank-details", response_model=SuccessResponse[VendorOut])
def update_bank_details(
    payload: VendorBankDetails, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)
):
    vendor = VendorService(db).update_bank_details(current_user.id, payload)
    return SuccessResponse(message="Bank details updated", data=VendorOut.model_validate(vendor))


@router.get("/nearby", response_model=SuccessResponse[list[VendorOut]])
def nearby_vendors(
    lat: float = Query(...), lng: float = Query(...), radius_km: float = Query(10.0), db: Session = Depends(get_db)
):
    vendors = VendorService(db).nearby_vendors(lat, lng, radius_km)
    return SuccessResponse(data=[VendorOut.model_validate(v) for v in vendors])


@router.get("/{slug}", response_model=SuccessResponse[VendorOut])
def get_store(slug: str, db: Session = Depends(get_db)):
    vendor = VendorService(db).get_public_profile(slug)
    return SuccessResponse(data=VendorOut.model_validate(vendor))


# ---- Admin ----
@router.post("/{vendor_id}/approve", response_model=SuccessResponse[VendorOut], dependencies=[Depends(require_admin)])
def approve_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    vendor = VendorService(db).approve(vendor_id)
    return SuccessResponse(message="Vendor approved", data=VendorOut.model_validate(vendor))


@router.post("/{vendor_id}/suspend", response_model=SuccessResponse[VendorOut], dependencies=[Depends(require_admin)])
def suspend_vendor(vendor_id: UUID, db: Session = Depends(get_db)):
    vendor = VendorService(db).suspend(vendor_id)
    return SuccessResponse(message="Vendor suspended", data=VendorOut.model_validate(vendor))
