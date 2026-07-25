import re
import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyExistsError, ForbiddenError, NotFoundError
from app.modules.vendors.models import Vendor, VendorStatus
from app.modules.vendors.repository import VendorRepository
from app.modules.vendors.schemas import VendorBankDetails, VendorRegister, VendorUpdate


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"{base}-{uuid.uuid4().hex[:6]}"


class VendorService:
    def __init__(self, db: Session):
        self.db = db
        self.vendors = VendorRepository(db)

    def register_vendor(self, owner_id: UUID, payload: VendorRegister) -> Vendor:
        if self.vendors.get_by_owner(owner_id):
            raise AlreadyExistsError("This user already has a vendor store")
        vendor = Vendor(owner_id=owner_id, slug=_slugify(payload.shop_name), **payload.model_dump())
        return self.vendors.create(vendor)

    def get_my_store(self, owner_id: UUID) -> Vendor:
        vendor = self.vendors.get_by_owner(owner_id)
        if not vendor:
            raise NotFoundError("Vendor store not found")
        return vendor

    def update_store(self, owner_id: UUID, payload: VendorUpdate) -> Vendor:
        vendor = self.get_my_store(owner_id)
        return self.vendors.update(vendor, **payload.model_dump(exclude_unset=True))

    def update_bank_details(self, owner_id: UUID, payload: VendorBankDetails) -> Vendor:
        vendor = self.get_my_store(owner_id)
        return self.vendors.update(vendor, **payload.model_dump())

    def get_public_profile(self, slug: str) -> Vendor:
        vendor = self.vendors.get_by_slug(slug)
        if not vendor or vendor.status != VendorStatus.APPROVED:
            raise NotFoundError("Store not found")
        return vendor

    def nearby_vendors(self, lat: float, lng: float, radius_km: float) -> list[Vendor]:
        return self.vendors.nearby(lat, lng, radius_km)

    # ---- Admin actions ----
    def approve(self, vendor_id: UUID) -> Vendor:
        vendor = self._get_or_404(vendor_id)
        return self.vendors.update(vendor, status=VendorStatus.APPROVED, is_verified=True)

    def suspend(self, vendor_id: UUID) -> Vendor:
        vendor = self._get_or_404(vendor_id)
        return self.vendors.update(vendor, status=VendorStatus.SUSPENDED)

    def reject(self, vendor_id: UUID) -> Vendor:
        vendor = self._get_or_404(vendor_id)
        return self.vendors.update(vendor, status=VendorStatus.REJECTED)

    def _get_or_404(self, vendor_id: UUID) -> Vendor:
        vendor = self.vendors.get(vendor_id)
        if not vendor:
            raise NotFoundError("Vendor not found")
        return vendor
