from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.products.models import Product, ProductVariant
from app.modules.products.repository import ProductRepository, ProductVariantRepository
from app.modules.products.schemas import ProductCreate, ProductUpdate
from app.modules.vendors.repository import VendorRepository


class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.products = ProductRepository(db)
        self.variants = ProductVariantRepository(db)
        self.vendors = VendorRepository(db)

    def _vendor_for(self, owner_id: UUID):
        vendor = self.vendors.get_by_owner(owner_id)
        if not vendor:
            raise NotFoundError("Vendor store not found for this user")
        return vendor

    def create_product(self, owner_id: UUID, payload: ProductCreate) -> Product:
        vendor = self._vendor_for(owner_id)
        data = payload.model_dump(exclude={"variants"})
        product = Product(vendor_id=vendor.id, **data)
        product = self.products.create(product)
        for variant_data in payload.variants:
            self.variants.create(ProductVariant(product_id=product.id, **variant_data.model_dump()))
        return self.products.get_with_variants(product.id)

    def update_product(self, owner_id: UUID, product_id: UUID, payload: ProductUpdate) -> Product:
        product = self._own_product_or_404(owner_id, product_id)
        return self.products.update(product, **payload.model_dump(exclude_unset=True))

    def delete_product(self, owner_id: UUID, product_id: UUID) -> None:
        product = self._own_product_or_404(owner_id, product_id)
        self.products.soft_delete(product)

    def get_product(self, product_id: UUID) -> Product:
        product = self.products.get_with_variants(product_id)
        if not product:
            raise NotFoundError("Product not found")
        return product

    def list_by_vendor(self, vendor_id: UUID) -> list[Product]:
        return self.products.list_by_vendor(vendor_id)

    def list_by_category(self, category_id: UUID) -> list[Product]:
        return self.products.list_by_category(category_id)

    def adjust_stock(self, owner_id: UUID, variant_id: UUID, delta: int) -> ProductVariant:
        variant = self.variants.get(variant_id)
        if not variant:
            raise NotFoundError("Variant not found")
        product = self._own_product_or_404(owner_id, variant.product_id)
        new_qty = max(0, variant.stock_qty + delta)
        return self.variants.update(variant, stock_qty=new_qty)

    def _own_product_or_404(self, owner_id: UUID, product_id: UUID) -> Product:
        vendor = self._vendor_for(owner_id)
        product = self.products.get(product_id)
        if not product:
            raise NotFoundError("Product not found")
        if product.vendor_id != vendor.id:
            raise ForbiddenError("You do not own this product")
        return product
