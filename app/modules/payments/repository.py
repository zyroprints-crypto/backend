from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.payments.models import Payment, VendorSettlement


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session):
        super().__init__(db, Payment)

    def get_by_order_id(self, order_id) -> Payment | None:
        stmt = select(Payment).where(Payment.order_id == order_id, Payment.is_deleted.is_(False))
        return self.db.execute(stmt).scalar_one_or_none()


class VendorSettlementRepository(BaseRepository[VendorSettlement]):
    def __init__(self, db: Session):
        super().__init__(db, VendorSettlement)
