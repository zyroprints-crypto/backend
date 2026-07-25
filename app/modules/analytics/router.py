from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dependencies import require_admin, require_vendor
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.analytics.schemas import PlatformAnalytics, VendorAnalytics
from app.modules.analytics.service import AnalyticsService
from app.modules.users.models import User
from app.modules.vendors.repository import VendorRepository

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/vendor/me", response_model=SuccessResponse[VendorAnalytics])
def my_vendor_analytics(current_user: User = Depends(require_vendor), db: Session = Depends(get_db)):
    vendor = VendorRepository(db).get_by_owner(current_user.id)
    data = AnalyticsService(db).vendor_analytics(vendor.id)
    return SuccessResponse(data=data)


@router.get("/platform", response_model=SuccessResponse[PlatformAnalytics], dependencies=[Depends(require_admin)])
def platform_analytics(db: Session = Depends(get_db)):
    data = AnalyticsService(db).platform_analytics()
    return SuccessResponse(data=data)
