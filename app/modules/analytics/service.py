from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.analytics.schemas import PlatformAnalytics, VendorAnalytics
from app.modules.orders.models import Order, OrderStatus
from app.modules.users.models import User
from app.modules.vendors.models import Vendor


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def vendor_analytics(self, vendor_id: UUID) -> VendorAnalytics:
        orders = self.db.execute(select(Order).where(Order.vendor_id == vendor_id, Order.is_deleted.is_(False))).scalars().all()
        completed = [o for o in orders if o.status == OrderStatus.COMPLETED]
        cancelled = [o for o in orders if o.status == OrderStatus.CANCELLED]
        revenue = sum(o.total_amount for o in completed)
        vendor = self.db.get(Vendor, vendor_id)
        return VendorAnalytics(
            total_orders=len(orders), completed_orders=len(completed), cancelled_orders=len(cancelled),
            total_revenue=revenue, average_rating=vendor.rating_avg if vendor else 0.0,
        )

    def platform_analytics(self) -> PlatformAnalytics:
        total_users = self.db.execute(select(func.count()).select_from(User).where(User.is_deleted.is_(False))).scalar_one()
        total_vendors = self.db.execute(select(func.count()).select_from(Vendor).where(Vendor.is_deleted.is_(False))).scalar_one()
        orders = self.db.execute(select(Order).where(Order.is_deleted.is_(False))).scalars().all()
        completed = [o for o in orders if o.status == OrderStatus.COMPLETED]
        revenue = sum(o.total_amount for o in completed)
        commission = sum(o.platform_commission for o in completed)
        return PlatformAnalytics(
            total_users=total_users, total_vendors=total_vendors, total_orders=len(orders),
            total_revenue=revenue, total_commission_earned=commission,
        )
