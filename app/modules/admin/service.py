from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.admin.repository import AuditLogRepository, CouponRepository, PlatformSettingRepository
from app.modules.admin.schemas import CouponCreate, PlatformSettingUpdate
from app.modules.orders.models import Coupon
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.vendors.models import VendorStatus
from app.modules.vendors.repository import VendorRepository


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.coupons = CouponRepository(db)
        self.audit = AuditLogRepository(db)
        self.settings = PlatformSettingRepository(db)
        self.users = UserRepository(db)
        self.vendors = VendorRepository(db)

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

    # ---- Vendors (approve/suspend live in VendorService; this adds audit + listing) ----
    def list_pending_vendors(self):
        return self.vendors.list_by_status(VendorStatus.PENDING, limit=100)

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
            from app.modules.admin.models import PlatformSetting
            updated = self.settings.create(PlatformSetting(key=key, value=payload.value))
        self.audit.record(actor_id, "setting.update", "platform_setting", key, payload.value)
        return updated

    def list_audit_logs(self, offset: int = 0, limit: int = 100):
        return self.audit.list(offset=offset, limit=limit)
