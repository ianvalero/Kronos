from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.document import DocumentDB
from app.models.document_version import DocumentVersionDB
from app.schemas.document import DocumentCreate, DocumentDelete

class DocumentRepository:
    def get_documents(self, session: Session, collection_id: int) -> list[DocumentDB]:
        statement = (
            select(DocumentDB)
            .where(
                DocumentDB.collection_id == collection_id,
                DocumentDB.deleted_at.is_(None)
            )
            .options(selectinload(
                DocumentDB.documents_versions.and_(DocumentVersionDB.status == "completed"))
            )
        )

        return session.exec(statement).all()

    def get_document(self, session: Session, document_id: int) -> DocumentDB | None:
        statement = (
            select(DocumentDB)
            .where(
                DocumentDB.id == document_id,
                DocumentDB.deleted_at.is_(None)
            )
            .options(selectinload(DocumentDB.documents_versions))
        )

        return session.exec(statement).first()

    def add_document(self, session: Session, document: DocumentCreate) -> DocumentDB:
        document: DocumentDB = DocumentDB(**document.model_dump())

        session.add(document)
        session.commit()
        session.refresh(document)

        return document

    def delete_document(self, session: Session, document_id: int, body: DocumentDelete) -> bool:
        document = self.get_document(session=session, document_id=document_id)
        if not document:
            return False

        document.deleted_at = datetime.now()
        document.deleted_by = body.deleted_by
        session.commit()

        return True
