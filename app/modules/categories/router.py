from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import require_admin
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.categories.schemas import CategoryCreate, CategoryOut
from app.modules.categories.service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=SuccessResponse[list[CategoryOut]])
def list_categories(db: Session = Depends(get_db)):
    categories = CategoryService(db).list_all()
    return SuccessResponse(data=[CategoryOut.model_validate(c) for c in categories])


@router.post("/", response_model=SuccessResponse[CategoryOut], status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    category = CategoryService(db).create(payload)
    return SuccessResponse(message="Category created", data=CategoryOut.model_validate(category))


@router.delete("/{category_id}", response_model=SuccessResponse, dependencies=[Depends(require_admin)])
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    CategoryService(db).delete(category_id)
    return SuccessResponse(message="Category deleted")
