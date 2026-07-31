from typing import cast
from datetime import datetime
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload

from app.models.document import DocumentDB
from app.models.document_version import DocumentVersionDB

class DocumentRepository:
    def get_documents(
        self,
        session: Session,
        collection_id: int,
        offset: int = 0,
        limit: int = 100
    ) -> tuple[list[DocumentDB], int]:
        where_conditions = (
            DocumentDB.collection_id == collection_id,
            DocumentDB.deleted_at.is_(None),
        )

        documents = (
            select(DocumentDB)
            .where(
                DocumentDB.collection_id == collection_id,
                DocumentDB.deleted_at.is_(None)
            )
            .options(
                selectinload(DocumentDB.documents_versions.and_(DocumentVersionDB.status == "ACTIVE")),
                selectinload(DocumentDB.collection)
            )
            .order_by(DocumentDB.id)
            .offset(offset)
            .limit(limit)
        )

        total = (
            select(func.count())
            .select_from(DocumentDB)
            .where(*where_conditions)
        )

        documents = cast(list[DocumentDB], session.exec(documents).all())
        total = cast(int, session.exec(total).one())
        return documents, total

    def get_document(self, session: Session, document_id: int) -> DocumentDB | None:
        statement = (
            select(DocumentDB)
            .where(
                DocumentDB.id == document_id,
                DocumentDB.deleted_at.is_(None)
            )
            .options(
                selectinload(DocumentDB.documents_versions),
                selectinload(DocumentDB.collection)
            )
        )

        return session.exec(statement).first()

    def add_document(self, session: Session, document: DocumentDB) -> DocumentDB:
        session.add(document)
        session.flush()
        return document

    def update_document(self, session: Session, document: DocumentDB) -> DocumentDB:
        document.updated_at = datetime.now()
        session.add(document)
        session.flush()
        return document

    def delete_document(self, session: Session, document: DocumentDB) -> bool:
        document.deleted_at = datetime.now()
        session.flush()
        return True
