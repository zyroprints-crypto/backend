from uuid import UUID
import secrets

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.security import hash_password
from app.modules.admin.pricing_config import get_all_rates_with_defaults, set_rate
from app.modules.admin.models import Banner, City, PlatformSetting
from app.modules.admin.repository import (
    AuditLogRepository,
    BannerRepository,
    CityRepository,
    ComplaintRepository,
    CouponRepository,
    LoginEventRepository,
    PlatformSettingRepository,
)
from app.modules.admin.schemas import (
    BannerCreate,
    BannerUpdate,
    CityCreate,
    ComplaintUpdate,
    CouponCreate,
    MaintenanceModeUpdate,
    PlatformSettingUpdate,
    VendorAdminCreate,
    VendorAdminUpdate,
)
from app.modules.orders.models import Coupon, Order, OrderStatus
from app.modules.orders.repository import OrderRepository
from app.modules.payments.models import Payment, PaymentStatus
from app.modules.payments.repository import PaymentRepository
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository
from app.modules.vendors.models import Vendor, VendorStatus
from app.modules.vendors.repository import VendorRepository
from app.modules.vendors.service import _slugify


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.coupons = CouponRepository(db)
        self.audit = AuditLogRepository(db)
        self.settings = PlatformSettingRepository(db)
        self.users = UserRepository(db)
        self.vendors = VendorRepository(db)
        self.cities = CityRepository(db)
        self.banners = BannerRepository(db)
        self.complaints = ComplaintRepository(db)
        self.orders = OrderRepository(db)
        self.payments = PaymentRepository(db)
        self.login_events = LoginEventRepository(db)

    # ---- Coupons ----
    def create_coupon(self, actor_id: UUID, payload: CouponCreate) -> Coupon:
        coupon = self.coupons.create(Coupon(**payload.model_dump()))
        self.audit.record(actor_id, "coupon.create", "coupon", str(coupon.id), payload.code)
        return coupon

    def list_coupons(self) -> list[Coupon]:
        return self.coupons.list(limit=200)

    def deactivate_coupon(self, actor_id: UUID, coupon_id: UUID) -> Coupon:
        coupon = self.coupons.get(coupon_id)
        if not coupon:
            raise NotFoundError("Coupon not found")
        updated = self.coupons.update(coupon, is_active=False)
        self.audit.record(actor_id, "coupon.deactivate", "coupon", str(coupon_id))
        return updated

    # ---- Customers ----
    def list_customers(self, offset: int = 0, limit: int = 50) -> list[User]:
        return self.users.list(offset=offset, limit=limit, role="customer")

    def suspend_user(self, actor_id: UUID, user_id: UUID) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        updated = self.users.update(user, is_active=False)
        self.audit.record(actor_id, "user.suspend", "user", str(user_id))
        return updated

    def reactivate_user(self, actor_id: UUID, user_id: UUID) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        updated = self.users.update(user, is_active=True)
        self.audit.record(actor_id, "user.reactivate", "user", str(user_id))
        return updated

    def delete_customer(self, actor_id: UUID, user_id: UUID) -> None:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        self.users.soft_delete(user)
        self.audit.record(actor_id, "user.delete", "user", str(user_id))

    # ---- Vendors (approve/suspend/reject live in VendorService; this adds
    # audit + listing + the admin-only create/edit/delete actions) ----
    def list_pending_vendors(self):
        return self.vendors.list_by_status(VendorStatus.PENDING, limit=100)

    def list_all_vendors(self):
        """Every vendor regardless of status — for the admin's full directory view."""
        return self.vendors.list_all(limit=500)

    def admin_create_vendor(self, actor_id: UUID, payload: VendorAdminCreate) -> Vendor:
        """Admin manually onboards a vendor without the normal self-serve
        registration flow — auto-approved since an admin is creating it directly."""
        owner = self.users.get_by_email(payload.owner_email)
        if not owner:
            owner = self.users.create(User(
                full_name=payload.owner_full_name, email=payload.owner_email, phone=payload.phone,
                hashed_password=hash_password(secrets.token_urlsafe(32)),  # unusable placeholder; owner signs in via OTP
                role=UserRole.VENDOR, is_active=True,
            ))
        elif self.vendors.get_by_owner(owner.id):
            raise ValidationAppError("This user already owns a vendor store")

        vendor = Vendor(
            owner_id=owner.id, shop_name=payload.shop_name, slug=_slugify(payload.shop_name),
            address_line=payload.address_line, city=payload.city, state=payload.state,
            pincode=payload.pincode, latitude=payload.latitude, longitude=payload.longitude,
            phone=payload.phone, gst_number=payload.gst_number,
            status=VendorStatus.APPROVED, is_verified=True,
        )
        vendor = self.vendors.create(vendor)
        self.audit.record(actor_id, "vendor.admin_create", "vendor", str(vendor.id), payload.shop_name)
        return vendor

    def admin_update_vendor(self, actor_id: UUID, vendor_id: UUID, payload: VendorAdminUpdate) -> Vendor:
        vendor = self.vendors.get(vendor_id)
        if not vendor:
            raise NotFoundError("Vendor not found")
        updated = self.vendors.update(vendor, **payload.model_dump(exclude_unset=True))
        self.audit.record(actor_id, "vendor.admin_update", "vendor", str(vendor_id))
        return updated

    def admin_delete_vendor(self, actor_id: UUID, vendor_id: UUID) -> None:
        vendor = self.vendors.get(vendor_id)
        if not vendor:
            raise NotFoundError("Vendor not found")
        self.vendors.soft_delete(vendor)
        self.audit.record(actor_id, "vendor.delete", "vendor", str(vendor_id))

    # ---- Orders (full platform visibility + override powers) ----
    def list_all_orders(self, offset: int = 0, limit: int = 200) -> list[Order]:
        return self.orders.list_all(offset=offset, limit=limit)

    def admin_cancel_order(self, actor_id: UUID, order_id: UUID, reason: str | None = None) -> Order:
        order = self.orders.get_with_items(order_id)
        if not order:
            raise NotFoundError("Order not found")
        if order.status in (OrderStatus.DELIVERED, OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            raise ValidationAppError(f"Cannot cancel an order that is already {order.status.value}")
        updated = self.orders.update(order, status=OrderStatus.CANCELLED)
        self.audit.record(actor_id, "order.admin_cancel", "order", str(order_id), reason)
        return self.orders.get_with_items(updated.id)

    def refund_order(self, actor_id: UUID, order_id: UUID, reason: str | None = None) -> Payment:
        order = self.orders.get(order_id)
        if not order:
            raise NotFoundError("Order not found")
        payment = self.payments.get_by_order_id(order_id)
        if not payment:
            raise NotFoundError("No payment record found for this order")
        if payment.status != PaymentStatus.SUCCESS:
            raise ValidationAppError(f"Cannot refund a payment with status '{payment.status.value}'")
        updated = self.payments.update(payment, status=PaymentStatus.REFUNDED)
        self.audit.record(actor_id, "order.refund", "payment", str(payment.id), reason)
        return updated

    # ---- Cities ----
    def create_city(self, actor_id: UUID, payload: CityCreate):
        city = self.cities.create(City(**payload.model_dump()))
        self.audit.record(actor_id, "city.create", "city", str(city.id), payload.name)
        return city

    def list_cities(self):
        return self.cities.list(limit=500)

    def remove_city(self, actor_id: UUID, city_id: UUID) -> None:
        city = self.cities.get(city_id)
        if not city:
            raise NotFoundError("City not found")
        self.cities.soft_delete(city)
        self.audit.record(actor_id, "city.remove", "city", str(city_id))

    # ---- Banners ----
    def create_banner(self, actor_id: UUID, payload: BannerCreate):
        banner = self.banners.create(Banner(**payload.model_dump()))
        self.audit.record(actor_id, "banner.create", "banner", str(banner.id), payload.title)
        return banner

    def list_banners(self, active_only: bool = False):
        return self.banners.list_active() if active_only else self.banners.list(limit=200)

    def update_banner(self, actor_id: UUID, banner_id: UUID, payload: BannerUpdate):
        banner = self.banners.get(banner_id)
        if not banner:
            raise NotFoundError("Banner not found")
        updated = self.banners.update(banner, **payload.model_dump(exclude_unset=True))
        self.audit.record(actor_id, "banner.update", "banner", str(banner_id))
        return updated

    def delete_banner(self, actor_id: UUID, banner_id: UUID) -> None:
        banner = self.banners.get(banner_id)
        if not banner:
            raise NotFoundError("Banner not found")
        self.banners.soft_delete(banner)
        self.audit.record(actor_id, "banner.delete", "banner", str(banner_id))

    # ---- Complaints ----
    def list_complaints(self, offset: int = 0, limit: int = 100):
        return self.complaints.list(offset=offset, limit=limit)

    def update_complaint(self, actor_id: UUID, complaint_id: UUID, payload: ComplaintUpdate):
        complaint = self.complaints.get(complaint_id)
        if not complaint:
            raise NotFoundError("Complaint not found")
        updated = self.complaints.update(
            complaint, status=payload.status, resolution_note=payload.resolution_note
        )
        self.audit.record(actor_id, "complaint.update", "complaint", str(complaint_id), payload.status)
        return updated

    # ---- Pricing rules ----
    def get_pricing_rates(self) -> dict[str, float]:
        return get_all_rates_with_defaults(self.db)

    def update_pricing_rate(self, actor_id: UUID, field_name: str, value: float) -> float:
        try:
            result = set_rate(self.db, field_name, value)
        except ValueError as exc:
            raise ValidationAppError(str(exc)) from exc
        self.audit.record(actor_id, "pricing.update", "pricing_rate", field_name, str(value))
        return result

    # ---- Maintenance mode ----
    def get_maintenance_mode(self) -> dict:
        setting = self.settings.get_by_key("maintenance_mode")
        message_setting = self.settings.get_by_key("maintenance_message")
        return {
            "enabled": setting.value == "true" if setting else False,
            "message": message_setting.value if message_setting else None,
        }

    def set_maintenance_mode(self, actor_id: UUID, payload: MaintenanceModeUpdate) -> dict:
        self.upsert_setting(actor_id, "maintenance_mode", PlatformSettingUpdate(value=str(payload.enabled).lower()))
        if payload.message is not None:
            self.upsert_setting(actor_id, "maintenance_message", PlatformSettingUpdate(value=payload.message))
        return self.get_maintenance_mode()

    # ---- Platform settings ----
    def get_setting(self, key: str):
        setting = self.settings.get_by_key(key)
        if not setting:
            raise NotFoundError(f"Setting '{key}' not found")
        return setting

    def upsert_setting(self, actor_id: UUID, key: str, payload: PlatformSettingUpdate):
        setting = self.settings.get_by_key(key)
        if setting:
            updated = self.settings.update(setting, value=payload.value)
        else:
            updated = self.settings.create(PlatformSetting(key=key, value=payload.value))
        self.audit.record(actor_id, "setting.update", "platform_setting", key, payload.value)
        return updated

    def list_audit_logs(self, offset: int = 0, limit: int = 100):
        return self.audit.list(offset=offset, limit=limit)

    def list_login_events(self, offset: int = 0, limit: int = 200):
        return self.login_events.list(offset=offset, limit=limit)
