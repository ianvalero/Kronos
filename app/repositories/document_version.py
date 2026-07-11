from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.document_version import DocumentVersionDB

class DocumentVersionRepository:
    def get_document_versions(self, session: Session, document_id: int) -> list[DocumentVersionDB]:
        statement = (
            select(DocumentVersionDB)
            .where(DocumentVersionDB.document_id == document_id)
            .order_by(DocumentVersionDB.id.desc())
        )

        return session.exec(statement).all()

    def get_document_active_versions(self, session: Session, document_id: int) -> list[DocumentVersionDB]:
        statement = (
            select(DocumentVersionDB)
            .where(
                DocumentVersionDB.document_id == document_id,
                DocumentVersionDB.status == "ACTIVE",
            )
            .order_by(DocumentVersionDB.id.desc())
        )

        return session.exec(statement).all()

    def get_document_version(self, session: Session, document_version_id: int) -> DocumentVersionDB | None:
        statement = (
            select(DocumentVersionDB)
            .options(selectinload(DocumentVersionDB.document))
            .where(DocumentVersionDB.id == document_version_id)
        )

        return session.exec(statement).first()

    def add_document_version(self, session: Session, document_version: DocumentVersionDB) -> DocumentVersionDB:
        session.add(document_version)
        session.flush()
        return document_version

    def set_document_version_task_id(
        self,
        session: Session,
        document_version: DocumentVersionDB,
        task_id: str
    ) -> DocumentVersionDB:
        document_version.task_id = task_id
        session.flush()
        return document_version

    def update_version_as_processing(
        self,
        session: Session,
        document_version: DocumentVersionDB
    ) -> DocumentVersionDB:
        document_version.status = "PROCESSING"

        session.flush()
        return document_version

    def update_version_as_active(
        self,
        session: Session,
        document_version: DocumentVersionDB,
        qdrant_point_ids: list[str]
    ) -> DocumentVersionDB:
        document_version.status = "ACTIVE"
        document_version.qdrant_point_ids = qdrant_point_ids
        document_version.error_message = None

        session.flush()
        return document_version

    def update_version_as_failed(
        self,
        session: Session,
        document_version: DocumentVersionDB,
        error_message: str
    ) -> DocumentVersionDB:
        document_version.status = "FAILED"
        document_version.error_message = error_message
        document_version.attempts += 1

        session.flush()
        return document_version

    def update_version_as_archived(
        self,
        session: Session,
        document_version: DocumentVersionDB
    ) -> DocumentVersionDB:
        document_version.status = "ARCHIVED"

        session.flush()
        return document_version