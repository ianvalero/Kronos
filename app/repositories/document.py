from typing import cast
from datetime import datetime
from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload

from app.models.document import DocumentDB
from app.models.document_version import DocumentVersionDB
from app.schemas.document import DocumentFilters

class DocumentRepository:
    def get_documents(
        self,
        session: Session,
        collection_ids: list[int],
        offset: int = 0,
        limit: int = 100,
        filters: DocumentFilters | None = None,
    ) -> tuple[list[DocumentDB], int]:
        where_conditions = [DocumentDB.collection_id.in_(collection_ids)]
        where_conditions += self.__generate_filters(filters)

        documents = (
            select(DocumentDB)
            .where(*where_conditions)
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

    def __generate_filters(self, filters: DocumentFilters | None = None) -> list:
        where_conditions = []

        if filters:
            if filters.collection_id:
                where_conditions.append(DocumentDB.collection_id == filters.collection_id)
            if filters.description:
                where_conditions.append(DocumentDB.description.ilike(f"%{filters.description}%"))
            if filters.created_by:
                where_conditions.append(DocumentDB.created_by == filters.created_by)
            if filters.created_at_from:
                where_conditions.append(DocumentDB.created_at >= filters.created_at_from)
            if filters.created_at_to:
                where_conditions.append(DocumentDB.created_at <= filters.created_at_to)

            if filters.is_deleted:
                where_conditions.append(DocumentDB.deleted_at.is_not(None))
            else:
                where_conditions.append(DocumentDB.deleted_at.is_(None))

        return where_conditions
