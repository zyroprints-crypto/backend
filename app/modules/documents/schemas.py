from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.documents.models import BindingType, ColorMode, DocumentStatus, FileType, SideMode


class PrintSettings(BaseModel):
    color_mode: ColorMode = ColorMode.BLACK_WHITE
    paper_size: str = "A4"
    paper_gsm: int = 75
    copies: int = Field(default=1, ge=1, le=1000)
    side_mode: SideMode = SideMode.SINGLE
    binding: BindingType = BindingType.NONE
    lamination: bool = False
    cover_page: bool = False
    premium_paper: bool = False
    express_delivery: bool = False


class DocumentUploadMeta(PrintSettings):
    file_name: str
    file_type: FileType
    file_size_bytes: int = 0
    page_count: int = Field(default=1, ge=1)


class DocumentUpdateSettings(PrintSettings):
    pass


class PrintDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    file_url: str
    file_name: str
    file_type: FileType
    page_count: int
    color_mode: ColorMode
    paper_size: str
    paper_gsm: int
    copies: int
    side_mode: SideMode
    binding: BindingType
    lamination: bool
    cover_page: bool
    premium_paper: bool
    express_delivery: bool
    status: DocumentStatus
    calculated_price: int
    ai_notes: str | None = None


class PriceEstimateResponse(BaseModel):
    calculated_price: int
    currency: str = "INR"
    price_display: str
