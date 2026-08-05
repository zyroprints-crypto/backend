from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.vendors.models import Vendor, VendorStatus


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, db: Session):
        super().__init__(db, Vendor)

    def get_by_owner(self, owner_id) -> Vendor | None:
        stmt = select(Vendor).where(Vendor.owner_id == owner_id, Vendor.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Vendor | None:
        stmt = select(Vendor).where(Vendor.slug == slug, Vendor.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_status(self, status: VendorStatus, offset: int = 0, limit: int = 20) -> list[Vendor]:
        return self.list(offset=offset, limit=limit, status=status)

    def list_all(self, offset: int = 0, limit: int = 200) -> list[Vendor]:
        """Every vendor regardless of status — admin directory view."""
        return self.list(offset=offset, limit=limit)

    def nearby(self, lat: float, lng: float, radius_km: float = 10.0, limit: int = 50) -> list[Vendor]:
        """
        Simple bounding-box + haversine filter in Python. For production scale,
        replace with PostGIS ST_DWithin on a geography column + a GIST index.
        """
        import math

        candidates = self.list(offset=0, limit=1000, status=VendorStatus.APPROVED)
        results = []
        for v in candidates:
            dlat, dlng = math.radians(v.latitude - lat), math.radians(v.longitude - lng)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(lat)) * math.cos(math.radians(v.latitude)) * math.sin(dlng / 2) ** 2
            )
            distance_km = 6371 * 2 * math.asin(math.sqrt(a))
            if distance_km <= radius_km:
                results.append(v)
        return results[:limit]
