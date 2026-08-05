from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.common.base_repository import BaseRepository
from app.modules.products.models import Product, ProductVariant


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session):
        super().__init__(db, Product)

    def get_with_variants(self, product_id):
        stmt = (
            select(Product)
            .options(selectinload(Product.variants))
            .where(Product.id == product_id, Product.is_deleted.is_(False))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_vendor(self, vendor_id, offset=0, limit=20):
        return self.list(offset=offset, limit=limit, vendor_id=vendor_id)

    def list_by_category(self, category_id, offset=0, limit=20):
        return self.list(offset=offset, limit=limit, category_id=category_id)


class ProductVariantRepository(BaseRepository[ProductVariant]):
    def __init__(self, db: Session):
        super().__init__(db, ProductVariant)
