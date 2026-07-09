import logging
from datetime import datetime

from sqlmodel import Session

from app.services import DocumentService
from app.repositories.document_version import DocumentVersionRepository
from app.models.document import DocumentDB
from app.infrastructure.celery_client import CeleryClient
from app.schemas.document import DocumentRead, DocumentCreate, DocumentDelete
from app.schemas.user import User
from app.exceptions import DocumentNotFoundError


class DocumentVersionService:
    def __init__(self, celery_client: CeleryClient, document_service: DocumentService):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.celery = celery_client
        self.document_service = document_service
        self.document_version_repository = DocumentVersionRepository()
        self.logger.info("Document Version Service initialized")

    def get_document_versions(self, session: Session, user: User, document_id: int):
        document_version_db = self.document_version_repository.get_document_versions(session, document_id)
        document_db = self.document_service.get_document(session, user, document_id)

    def get_document_version(self, session: Session, user: User, document_id: int, document_version_id: int):
        pass

    def add_document_version(self):
        pass