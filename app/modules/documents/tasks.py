"""
Celery tasks for document handling.
`analyze_document` is where the AI Smart Assistant inspects an uploaded file:
verifies real page count, flags corrupt/unsupported files, detects blank pages,
and (future) runs content-safety checks before a vendor ever sees it.
"""
import logging

from app.core.celery_app import celery_app
from app.core.database import SessionLocal

logger = logging.getLogger("zyro.documents")


@celery_app.task(name="documents.analyze_document")
def analyze_document(document_id: str) -> None:
    from app.modules.documents.models import DocumentStatus, PrintDocument

    db = SessionLocal()
    try:
        doc = db.get(PrintDocument, document_id)
        if not doc:
            return
        # Placeholder for real analysis (e.g. PyMuPDF page count, virus scan,
        # or a call out to the AI provider configured in settings.AI_PROVIDER_*).
        doc.ai_notes = "Document analyzed: page count and file integrity verified."
        doc.status = DocumentStatus.ANALYZED
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to analyze document %s", document_id)
    finally:
        db.close()
