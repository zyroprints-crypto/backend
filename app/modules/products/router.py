from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user, require_vendor
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.products.schemas import ProductCreate, ProductOut, ProductUpdate
from app.modules.products.service import ProductService
from app.modules.users.models import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=SuccessResponse[ProductOut], status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)):
    product = ProductService(db).create_product(current_user.id, payload)
    return SuccessResponse(message="Product created", data=ProductOut.model_validate(product))


@router.patch("/{product_id}", response_model=SuccessResponse[ProductOut])
def update_product(
    product_id: UUID, payload: ProductUpdate, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)
):
    product = ProductService(db).update_product(current_user.id, product_id, payload)
    return SuccessResponse(message="Product updated", data=ProductOut.model_validate(product))


@router.delete("/{product_id}", response_model=SuccessResponse)
def delete_product(product_id: UUID, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)):
    ProductService(db).delete_product(current_user.id, product_id)
    return SuccessResponse(message="Product deleted")


@router.get("/{product_id}", response_model=SuccessResponse[ProductOut])
def get_product(product_id: UUID, db: Session = Depends(get_db)):
    product = ProductService(db).get_product(product_id)
    return SuccessResponse(data=ProductOut.model_validate(product))


@router.get("/vendor/{vendor_id}", response_model=SuccessResponse[list[ProductOut]])
def list_vendor_products(vendor_id: UUID, db: Session = Depends(get_db)):
    products = ProductService(db).list_by_vendor(vendor_id)
    return SuccessResponse(data=[ProductOut.model_validate(p) for p in products])


@router.get("/category/{category_id}", response_model=SuccessResponse[list[ProductOut]])
def list_category_products(category_id: UUID, db: Session = Depends(get_db)):
    products = ProductService(db).list_by_category(category_id)
    return SuccessResponse(data=[ProductOut.model_validate(p) for p in products])


@router.post("/variants/{variant_id}/adjust-stock", response_model=SuccessResponse)
def adjust_stock(
    variant_id: UUID, delta: int, current_user: User = Depends(require_vendor), db: Session = Depends(get_db)
):
    variant = ProductService(db).adjust_stock(current_user.id, variant_id, delta)
    return SuccessResponse(message="Stock updated", data={"variant_id": str(variant.id), "stock_qty": variant.stock_qty})
