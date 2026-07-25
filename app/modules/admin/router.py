from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import require_admin
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.admin.schemas import (
    AuditLogOut, CouponCreate, CouponOut, PlatformSettingOut, PlatformSettingUpdate,
)
from app.modules.admin.service import AdminService
from app.modules.users.models import User
from app.modules.users.schemas import UserOut
from app.modules.vendors.schemas import VendorOut

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


# ---- Coupons ----
@router.post("/coupons", response_model=SuccessResponse[CouponOut], status_code=status.HTTP_201_CREATED)
def create_coupon(payload: CouponCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    coupon = AdminService(db).create_coupon(current_user.id, payload)
    return SuccessResponse(message="Coupon created", data=CouponOut.model_validate(coupon))


@router.get("/coupons", response_model=SuccessResponse[list[CouponOut]])
def list_coupons(db: Session = Depends(get_db)):
    coupons = AdminService(db).list_coupons()
    return SuccessResponse(data=[CouponOut.model_validate(c) for c in coupons])


@router.delete("/coupons/{coupon_id}", response_model=SuccessResponse[CouponOut])
def deactivate_coupon(coupon_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    coupon = AdminService(db).deactivate_coupon(current_user.id, coupon_id)
    return SuccessResponse(message="Coupon deactivated", data=CouponOut.model_validate(coupon))


# ---- Customers ----
@router.get("/customers", response_model=SuccessResponse[list[UserOut]])
def list_customers(db: Session = Depends(get_db)):
    users = AdminService(db).list_customers()
    return SuccessResponse(data=[UserOut.model_validate(u) for u in users])


@router.post("/customers/{user_id}/suspend", response_model=SuccessResponse[UserOut])
def suspend_user(user_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = AdminService(db).suspend_user(current_user.id, user_id)
    return SuccessResponse(message="User suspended", data=UserOut.model_validate(user))


@router.post("/customers/{user_id}/reactivate", response_model=SuccessResponse[UserOut])
def reactivate_user(user_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = AdminService(db).reactivate_user(current_user.id, user_id)
    return SuccessResponse(message="User reactivated", data=UserOut.model_validate(user))


# ---- Vendors ----
@router.get("/vendors/pending", response_model=SuccessResponse[list[VendorOut]])
def pending_vendors(db: Session = Depends(get_db)):
    vendors = AdminService(db).list_pending_vendors()
    return SuccessResponse(data=[VendorOut.model_validate(v) for v in vendors])


# ---- Platform settings ----
@router.put("/settings/{key}", response_model=SuccessResponse[PlatformSettingOut])
def upsert_setting(
    key: str, payload: PlatformSettingUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    setting = AdminService(db).upsert_setting(current_user.id, key, payload)
    return SuccessResponse(message="Setting saved", data=PlatformSettingOut.model_validate(setting))


@router.get("/settings/{key}", response_model=SuccessResponse[PlatformSettingOut])
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = AdminService(db).get_setting(key)
    return SuccessResponse(data=PlatformSettingOut.model_validate(setting))


# ---- Audit log ----
@router.get("/audit-logs", response_model=SuccessResponse[list[AuditLogOut]])
def list_audit_logs(db: Session = Depends(get_db)):
    logs = AdminService(db).list_audit_logs()
    return SuccessResponse(data=[AuditLogOut.model_validate(l) for l in logs])
