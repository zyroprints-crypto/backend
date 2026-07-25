from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.common.storage import get_storage_backend, validate_upload
from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.documents.models import DocumentStatus, PrintDocument
from app.modules.documents.pricing import calculate_price
from app.modules.documents.repository import PrintDocumentRepository
from app.modules.documents.schemas import DocumentUpdateSettings, DocumentUploadMeta


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.documents = PrintDocumentRepository(db)
        self.storage = get_storage_backend()

    def upload_document(self, customer_id: UUID, file: UploadFile, meta: DocumentUploadMeta) -> PrintDocument:
        validate_upload(file.filename, meta.file_size_bytes)
        key = f"documents/{customer_id}/{file.filename}"
        url = self.storage.upload(file.file, key, file.content_type or "application/octet-stream")

        doc = PrintDocument(
            customer_id=customer_id,
            file_url=url,
            status=DocumentStatus.UPLOADED,
            **meta.model_dump(),
        )
        doc = self.documents.create(doc)
        doc.calculated_price = calculate_price(doc)
        doc.status = DocumentStatus.PRICED
        self.documents.update(doc, calculated_price=doc.calculated_price, status=doc.status)

        # Kick off async AI analysis (page-count verification, content-safety check, etc).
        from app.modules.documents.tasks import analyze_document
        analyze_document.delay(str(doc.id))

        return doc

    def update_settings(self, customer_id: UUID, document_id: UUID, payload: DocumentUpdateSettings) -> PrintDocument:
        doc = self._own_or_404(customer_id, document_id)
        updated = self.documents.update(doc, **payload.model_dump())
        price = calculate_price(updated)
        return self.documents.update(updated, calculated_price=price, status=DocumentStatus.PRICED)

    def estimate_price(self, customer_id: UUID, document_id: UUID) -> int:
        doc = self._own_or_404(customer_id, document_id)
        return calculate_price(doc)

    def get(self, customer_id: UUID, document_id: UUID) -> PrintDocument:
        return self._own_or_404(customer_id, document_id)

    def list_mine(self, customer_id: UUID) -> list[PrintDocument]:
        return self.documents.list(limit=100, customer_id=customer_id)

    def _own_or_404(self, customer_id: UUID, document_id: UUID) -> PrintDocument:
        doc = self.documents.get(document_id)
        if not doc:
            raise NotFoundError("Document not found")
        if doc.customer_id != customer_id:
            raise ForbiddenError("You do not own this document")
        return doc
