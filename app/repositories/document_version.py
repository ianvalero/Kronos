from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.document_version import DocumentVersionDB
from app.schemas.document_version import DocumentVersionCreate

class DocumentVersionRepository:
    def get_document_versions(self, session: Session, document_id: int) -> list[DocumentVersionDB]:
        statement = (
            select(DocumentVersionDB)
            .where(DocumentVersionDB.document_id == document_id)
            .order_by(DocumentVersionDB.id.desc())
        )

        return session.exec(statement).all()

    def get_document_completed_versions(self, session: Session, document_id: int) -> list[DocumentVersionDB]:
        statement = (
            select(DocumentVersionDB)
            .where(
                DocumentVersionDB.document_id == document_id,
                DocumentVersionDB.status == "completed",
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

    def add_document_version(
        self,
        session: Session,
        document_id: int,
        document_version: DocumentVersionCreate,
    ) -> DocumentVersionDB:
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

        return document_version

    def set_document_version_task_id(
        self,
        session: Session,
        document_version_id: int,
        task_id: str
    ) -> DocumentVersionDB | None:
        document_version = self.get_document_version(document_version_id, session)
        if not document_version:
            return None

        document_version.task_id = task_id
        session.commit()
        session.refresh(document_version)

        return document_version

    def update_document_version_status(
        self,
        document_version_id: int,
        status: str,
        session: Session,
        qdrant_point_ids: list[str] | None = None,
        error_message: str | None = None,
        increment_attempts: bool = False,
    ) -> DocumentVersionDB | None:
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

        return document_version
