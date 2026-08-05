from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.admin.models import AuditLog, Banner, City, Complaint, LoginEvent, PlatformSetting
from app.modules.orders.models import Coupon


class CouponRepository(BaseRepository[Coupon]):
    def __init__(self, db: Session):
        super().__init__(db, Coupon)


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(db, AuditLog)

    def record(self, actor_id, action: str, target_type: str | None = None, target_id: str | None = None,
               details: str | None = None) -> AuditLog:
        return self.create(AuditLog(actor_id=actor_id, action=action, target_type=target_type,
                                     target_id=target_id, details=details))


class PlatformSettingRepository(BaseRepository[PlatformSetting]):
    def __init__(self, db: Session):
        super().__init__(db, PlatformSetting)

    def get_by_key(self, key: str) -> PlatformSetting | None:
        stmt = select(PlatformSetting).where(PlatformSetting.key == key, PlatformSetting.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()


class CityRepository(BaseRepository[City]):
    def __init__(self, db: Session):
        super().__init__(db, City)

    def get_by_slug(self, slug: str) -> City | None:
        stmt = select(City).where(City.slug == slug, City.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()


class BannerRepository(BaseRepository[Banner]):
    def __init__(self, db: Session):
        super().__init__(db, Banner)

    def list_active(self) -> list[Banner]:
        stmt = (
            select(Banner)
            .where(Banner.is_active.is_(True), Banner.is_deleted.is_(False))
            .order_by(Banner.display_order)
        )
        return list(self.db.execute(stmt).scalars().all())


class ComplaintRepository(BaseRepository[Complaint]):
    def __init__(self, db: Session):
        super().__init__(db, Complaint)


class LoginEventRepository(BaseRepository[LoginEvent]):
    def __init__(self, db: Session):
        super().__init__(db, LoginEvent)

    def record(self, user_id, method: str, ip_address: str | None = None) -> LoginEvent:
        return self.create(LoginEvent(user_id=user_id, method=method, ip_address=ip_address))
