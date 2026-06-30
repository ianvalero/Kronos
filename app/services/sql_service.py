import logging
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.document import DocumentDB, DocumentVersionDB
from app.schemas.document import DocumentCreate, DocumentVersionCreate, DocumentDelete

class SqlService:
    def __init__(self):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.logger.info("SQL Service initialized")

    def get_documents(self, session: Session):
        try:
            return session.exec(select(DocumentDB).options(selectinload(DocumentDB.documents_versions))).all()
        except Exception as e:
            self.logger.error("Error fetching documents from database")
            self.logger.exception(e)
            raise

    def get_document(self, document_id: int, session: Session):
        try:
            document = session.exec(
                select(DocumentDB).options(selectinload(DocumentDB.documents_versions))
                .where(DocumentDB.id == document_id)
            ).first()
            return document
        except Exception as e:
            self.logger.error("Error fetching document from database")
            self.logger.exception(e)
            raise

    def get_document_version(self, document_version_id: int, session: Session):
        try:
            document_version = session.exec(
                select(DocumentVersionDB)
                .options(selectinload(DocumentVersionDB.document))
                .where(DocumentVersionDB.id == document_version_id)
            ).first()
            return document_version
        except Exception as e:
            self.logger.error("Error fetching document version from database")
            self.logger.exception(e)
            raise

    def add_document(self, document: DocumentCreate, session: Session):
        try:
            document: DocumentDB = DocumentDB(**document.model_dump())
            session.add(document)
            session.commit()
            session.refresh(document)

            self.logger.info(f"Document {document.id} added to database")
            return document
        except Exception as e:
            self.logger.error("Error adding document to database")
            self.logger.exception(e)
            raise

    def add_document_version(self, document_id: int, document_version: DocumentVersionCreate, session: Session):
        try:
            document_version: DocumentVersionDB = DocumentVersionDB(
                document_id=document_id,
                filename=Path(document_version.saved_file_path).name,
                original_filename=document_version.filename,
                file_path=document_version.saved_file_path,
                file_size=document_version.file_size,
                mime_type=document_version.mime_type,
                uploaded_by=document_version.uploaded_by,
            )

            session.add(document_version)
            session.commit()
            session.refresh(document_version)

            self.logger.info(f"Document version {document_version.id} added to database")
            return document_version

        except Exception as e:
            self.logger.error("Error adding document version to database")
            self.logger.exception(e)
            raise

    def set_document_version_task_id(self, document_version_id: int, task_id: str, session: Session):
        try:
            document_version = self.get_document_version(document_version_id, session)
            if not document_version:
                return None

            document_version.task_id = task_id
            session.commit()
            session.refresh(document_version)

            self.logger.info(f"Document version {document_version_id} linked to task {task_id}")
            return document_version
        except Exception as e:
            self.logger.error(f"Error setting task_id for document version {document_version_id}")
            self.logger.exception(e)
            raise

    def update_document_version_status(
        self,
        document_version_id: int,
        status: str,
        session: Session,
        qdrant_point_ids: list[int] | None = None,
        error_message: str | None = None,
        increment_attempts: bool = False,
    ):
        try:
            document_version = self.get_document_version(document_version_id, session)
            if not document_version:
                return None

            document_version.status = status
            document_version.error_message = error_message
            if qdrant_point_ids is not None:
                document_version.qdrant_point_ids = qdrant_point_ids
            if increment_attempts:
                document_version.attempts += 1

            session.commit()
            session.refresh(document_version)

            self.logger.info(f"Document version {document_version_id} updated to status={status}")
            return document_version
        except Exception as e:
            self.logger.error(f"Error updating document version {document_version_id} status")
            self.logger.exception(e)
            raise

    def delete_document(self, document_id: int, body: DocumentDelete, session: Session):
        try:
            document = self.get_document(document_id, session)
            if not document:
                return None

            document.deleted_at = datetime.now()
            document.deleted_by = body.deleted_by
            session.commit()

            self.logger.info(f"Document {document_id} marked as deleted in database")
            return True
        except Exception as e:
            self.logger.error("Error deleting document from database")
            self.logger.exception(e)
            raise
