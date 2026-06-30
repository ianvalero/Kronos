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
                original_filename=document_version.filename,
                file_path=document_version.save_file_path,
                file_size=document_version.file_size,
                mime_type=document_version.mime_type,
                **document_version.model_dump()
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
