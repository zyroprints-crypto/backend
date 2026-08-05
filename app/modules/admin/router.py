from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import require_admin
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.admin.schemas import (
    AuditLogOut,
    BannerCreate,
    BannerOut,
    BannerUpdate,
    CityCreate,
    CityOut,
    ComplaintOut,
    ComplaintUpdate,
    CouponCreate,
    CouponOut,
    LoginEventOut,
    MaintenanceModeOut,
    MaintenanceModeUpdate,
    PlatformSettingOut,
    PlatformSettingUpdate,
    PricingRateUpdate,
    PricingRatesOut,
    RefundRequest,
    VendorAdminCreate,
    VendorAdminUpdate,
)
from app.modules.admin.service import AdminService
from app.modules.orders.schemas import OrderOut
from app.modules.payments.schemas import PaymentOut
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


@router.delete("/customers/{user_id}", response_model=SuccessResponse)
def delete_customer(user_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    AdminService(db).delete_customer(current_user.id, user_id)
    return SuccessResponse(message="Customer deleted")


# ---- Vendors ----
@router.get("/vendors", response_model=SuccessResponse[list[VendorOut]])
def list_all_vendors(db: Session = Depends(get_db)):
    vendors = AdminService(db).list_all_vendors()
    return SuccessResponse(data=[VendorOut.model_validate(v) for v in vendors])


@router.get("/vendors/pending", response_model=SuccessResponse[list[VendorOut]])
def pending_vendors(db: Session = Depends(get_db)):
    vendors = AdminService(db).list_pending_vendors()
    return SuccessResponse(data=[VendorOut.model_validate(v) for v in vendors])


@router.post("/vendors", response_model=SuccessResponse[VendorOut], status_code=status.HTTP_201_CREATED)
def admin_create_vendor(
    payload: VendorAdminCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    vendor = AdminService(db).admin_create_vendor(current_user.id, payload)
    return SuccessResponse(message="Vendor created", data=VendorOut.model_validate(vendor))


@router.patch("/vendors/{vendor_id}", response_model=SuccessResponse[VendorOut])
def admin_update_vendor(
    vendor_id: UUID, payload: VendorAdminUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    vendor = AdminService(db).admin_update_vendor(current_user.id, vendor_id, payload)
    return SuccessResponse(message="Vendor updated", data=VendorOut.model_validate(vendor))


@router.delete("/vendors/{vendor_id}", response_model=SuccessResponse)
def admin_delete_vendor(vendor_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    AdminService(db).admin_delete_vendor(current_user.id, vendor_id)
    return SuccessResponse(message="Vendor deleted")


# ---- Orders (full platform visibility + override powers) ----
@router.get("/orders", response_model=SuccessResponse[list[OrderOut]])
def list_all_orders(db: Session = Depends(get_db)):
    orders = AdminService(db).list_all_orders()
    return SuccessResponse(data=[OrderOut.model_validate(o) for o in orders])


@router.post("/orders/{order_id}/cancel", response_model=SuccessResponse[OrderOut])
def admin_cancel_order(
    order_id: UUID, payload: RefundRequest, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    order = AdminService(db).admin_cancel_order(current_user.id, order_id, payload.reason)
    return SuccessResponse(message="Order cancelled", data=OrderOut.model_validate(order))


@router.post("/orders/{order_id}/refund", response_model=SuccessResponse[PaymentOut])
def refund_order(
    order_id: UUID, payload: RefundRequest, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    payment = AdminService(db).refund_order(current_user.id, order_id, payload.reason)
    return SuccessResponse(message="Refund recorded", data=PaymentOut.model_validate(payment))


# ---- Cities ----
@router.post("/cities", response_model=SuccessResponse[CityOut], status_code=status.HTTP_201_CREATED)
def create_city(payload: CityCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    city = AdminService(db).create_city(current_user.id, payload)
    return SuccessResponse(message="City added", data=CityOut.model_validate(city))


@router.get("/cities", response_model=SuccessResponse[list[CityOut]])
def list_cities(db: Session = Depends(get_db)):
    cities = AdminService(db).list_cities()
    return SuccessResponse(data=[CityOut.model_validate(c) for c in cities])


@router.delete("/cities/{city_id}", response_model=SuccessResponse)
def remove_city(city_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    AdminService(db).remove_city(current_user.id, city_id)
    return SuccessResponse(message="City removed")


# ---- Banners ----
@router.post("/banners", response_model=SuccessResponse[BannerOut], status_code=status.HTTP_201_CREATED)
def create_banner(payload: BannerCreate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    banner = AdminService(db).create_banner(current_user.id, payload)
    return SuccessResponse(message="Banner created", data=BannerOut.model_validate(banner))


@router.get("/banners", response_model=SuccessResponse[list[BannerOut]])
def list_banners(db: Session = Depends(get_db)):
    banners = AdminService(db).list_banners()
    return SuccessResponse(data=[BannerOut.model_validate(b) for b in banners])


@router.patch("/banners/{banner_id}", response_model=SuccessResponse[BannerOut])
def update_banner(
    banner_id: UUID, payload: BannerUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    banner = AdminService(db).update_banner(current_user.id, banner_id, payload)
    return SuccessResponse(message="Banner updated", data=BannerOut.model_validate(banner))


@router.delete("/banners/{banner_id}", response_model=SuccessResponse)
def delete_banner(banner_id: UUID, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    AdminService(db).delete_banner(current_user.id, banner_id)
    return SuccessResponse(message="Banner deleted")


# ---- Complaints ----
@router.get("/complaints", response_model=SuccessResponse[list[ComplaintOut]])
def list_complaints(db: Session = Depends(get_db)):
    complaints = AdminService(db).list_complaints()
    return SuccessResponse(data=[ComplaintOut.model_validate(c) for c in complaints])


@router.patch("/complaints/{complaint_id}", response_model=SuccessResponse[ComplaintOut])
def update_complaint(
    complaint_id: UUID, payload: ComplaintUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    complaint = AdminService(db).update_complaint(current_user.id, complaint_id, payload)
    return SuccessResponse(message="Complaint updated", data=ComplaintOut.model_validate(complaint))


# ---- Pricing rules ----
@router.get("/pricing", response_model=SuccessResponse[PricingRatesOut])
def get_pricing_rates(db: Session = Depends(get_db)):
    rates = AdminService(db).get_pricing_rates()
    return SuccessResponse(data=PricingRatesOut(rates=rates))


@router.put("/pricing/{field_name}", response_model=SuccessResponse[dict])
def update_pricing_rate(
    field_name: str, payload: PricingRateUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    value = AdminService(db).update_pricing_rate(current_user.id, field_name, payload.value)
    return SuccessResponse(message="Pricing rate updated", data={field_name: value})


# ---- Maintenance mode ----
@router.get("/maintenance-mode", response_model=SuccessResponse[MaintenanceModeOut])
def get_maintenance_mode(db: Session = Depends(get_db)):
    state = AdminService(db).get_maintenance_mode()
    return SuccessResponse(data=MaintenanceModeOut(**state))


@router.put("/maintenance-mode", response_model=SuccessResponse[MaintenanceModeOut])
def set_maintenance_mode(
    payload: MaintenanceModeUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    state = AdminService(db).set_maintenance_mode(current_user.id, payload)
    return SuccessResponse(message="Maintenance mode updated", data=MaintenanceModeOut(**state))


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


# ---- Login events ----
@router.get("/login-events", response_model=SuccessResponse[list[LoginEventOut]])
def list_login_events(db: Session = Depends(get_db)):
    events = AdminService(db).list_login_events()
    return SuccessResponse(data=[LoginEventOut.model_validate(e) for e in events])
