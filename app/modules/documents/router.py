from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.documents.models import BindingType, ColorMode, FileType, SideMode
from app.modules.documents.schemas import (
    DocumentUpdateSettings,
    DocumentUploadMeta,
    PriceEstimateResponse,
    PrintDocumentOut,
)
from app.modules.documents.service import DocumentService
from app.modules.users.models import User

router = APIRouter(prefix="/documents", tags=["Document Printing"])


def _upload_meta_form(
    file_name: str = Form(...),
    file_type: FileType = Form(...),
    file_size_bytes: int = Form(0),
    page_count: int = Form(1),
    color_mode: ColorMode = Form(ColorMode.BLACK_WHITE),
    paper_size: str = Form("A4"),
    paper_gsm: int = Form(75),
    copies: int = Form(1),
    side_mode: SideMode = Form(SideMode.SINGLE),
    binding: BindingType = Form(BindingType.NONE),
    lamination: bool = Form(False),
    cover_page: bool = Form(False),
    premium_paper: bool = Form(False),
    express_delivery: bool = Form(False),
) -> DocumentUploadMeta:
    """
    Multipart-form adapter: FastAPI can't bind a Pydantic model directly to
    multipart fields alongside a file upload, so each field is declared
    explicitly here and assembled into the DocumentUploadMeta schema.
    """
    return DocumentUploadMeta(
        file_name=file_name, file_type=file_type, file_size_bytes=file_size_bytes, page_count=page_count,
        color_mode=color_mode, paper_size=paper_size, paper_gsm=paper_gsm, copies=copies, side_mode=side_mode,
        binding=binding, lamination=lamination, cover_page=cover_page, premium_paper=premium_paper,
        express_delivery=express_delivery,
    )


@router.post("/upload", response_model=SuccessResponse[PrintDocumentOut], status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    meta: DocumentUploadMeta = Depends(_upload_meta_form),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = DocumentService(db).upload_document(current_user.id, file, meta)
    return SuccessResponse(message="File uploaded and priced", data=PrintDocumentOut.model_validate(doc))


@router.patch("/{document_id}/settings", response_model=SuccessResponse[PrintDocumentOut])
def update_print_settings(
    document_id: UUID,
    payload: DocumentUpdateSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = DocumentService(db).update_settings(current_user.id, document_id, payload)
    return SuccessResponse(message="Settings updated, price recalculated", data=PrintDocumentOut.model_validate(doc))


@router.get("/{document_id}/estimate", response_model=SuccessResponse[PriceEstimateResponse])
def estimate_price(document_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    price = DocumentService(db).estimate_price(current_user.id, document_id)
    return SuccessResponse(data=PriceEstimateResponse(calculated_price=price, price_display=f"₹{price / 100:.2f}"))


@router.get("/{document_id}", response_model=SuccessResponse[PrintDocumentOut])
def get_document(document_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = DocumentService(db).get(current_user.id, document_id)
    return SuccessResponse(data=PrintDocumentOut.model_validate(doc))


@router.get("/", response_model=SuccessResponse[list[PrintDocumentOut]])
def list_my_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    docs = DocumentService(db).list_mine(current_user.id)
    return SuccessResponse(data=[PrintDocumentOut.model_validate(d) for d in docs])
