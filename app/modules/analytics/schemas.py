from pydantic import BaseModel


class VendorAnalytics(BaseModel):
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: int  # paise
    average_rating: float


class PlatformAnalytics(BaseModel):
    total_users: int
    total_vendors: int
    total_orders: int
    total_revenue: int
    total_commission_earned: int
