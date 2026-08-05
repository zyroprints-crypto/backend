import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.common.db_types import GUID

from app.common.base_model import BaseEntity
from app.core.database import Base


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    PPT = "ppt"
    PPTX = "pptx"
    IMAGE = "image"


class ColorMode(str, enum.Enum):
    COLOR = "color"
    BLACK_WHITE = "black_white"


class SideMode(str, enum.Enum):
    SINGLE = "single"
    DOUBLE = "double"


class BindingType(str, enum.Enum):
    NONE = "none"
    SPIRAL = "spiral"
    STAPLE = "staple"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    ANALYZED = "analyzed"
    PRICED = "priced"
    ORDERED = "ordered"


class PrintDocument(Base, BaseEntity):
    """An uploaded file plus the print settings the customer chose, priced instantly."""
    __tablename__ = "print_documents"

    customer_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)

    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, name="file_type"), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=1)

    color_mode: Mapped[ColorMode] = mapped_column(Enum(ColorMode, name="color_mode"), default=ColorMode.BLACK_WHITE)
    paper_size: Mapped[str] = mapped_column(String(10), default="A4")  # A4, A3, Letter, Legal
    paper_gsm: Mapped[int] = mapped_column(Integer, default=75)  # 70/75/80/100/120
    copies: Mapped[int] = mapped_column(Integer, default=1)
    side_mode: Mapped[SideMode] = mapped_column(Enum(SideMode, name="side_mode"), default=SideMode.SINGLE)
    binding: Mapped[BindingType] = mapped_column(Enum(BindingType, name="binding_type"), default=BindingType.NONE)
    lamination: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_page: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_paper: Mapped[bool] = mapped_column(Boolean, default=False)
    express_delivery: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.UPLOADED
    )
    calculated_price: Mapped[int] = mapped_column(Integer, default=0)  # paise
    ai_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
