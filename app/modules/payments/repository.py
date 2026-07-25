from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.payments.models import Payment, VendorSettlement


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session):
        super().__init__(db, Payment)


class VendorSettlementRepository(BaseRepository[VendorSettlement]):
    def __init__(self, db: Session):
        super().__init__(db, VendorSettlement)
