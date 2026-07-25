from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.documents.models import PrintDocument


class PrintDocumentRepository(BaseRepository[PrintDocument]):
    def __init__(self, db: Session):
        super().__init__(db, PrintDocument)
