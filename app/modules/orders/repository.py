from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.common.base_repository import BaseRepository
from app.modules.orders.models import Order, OrderItem, OrderStatusEvent


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(db, Order)

    def get_with_items(self, order_id):
        stmt = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.status_history))
            .where(Order.id == order_id, Order.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_customer(self, customer_id, offset=0, limit=20):
        return self.list(offset=offset, limit=limit, customer_id=customer_id)

    def list_for_vendor(self, vendor_id, offset=0, limit=20):
        return self.list(offset=offset, limit=limit, vendor_id=vendor_id)

    def list_all(self, offset=0, limit=200):
        """Every order platform-wide — admin visibility only."""
        return self.list(offset=offset, limit=limit)


class OrderItemRepository(BaseRepository[OrderItem]):
    def __init__(self, db: Session):
        super().__init__(db, OrderItem)


class OrderStatusEventRepository(BaseRepository[OrderStatusEvent]):
    def __init__(self, db: Session):
        super().__init__(db, OrderStatusEvent)
