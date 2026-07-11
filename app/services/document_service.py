import logging
from datetime import datetime

from sqlmodel import Session

from app.services import CollectionService
from app.repositories.document import DocumentRepository
from app.models.document import DocumentDB
from app.infrastructure.qdrant_gateway import QdrantGateway
from app.schemas.document import DocumentRead, DocumentCreate
from app.schemas.user import User
from app.exceptions import DocumentNotFoundError, QdrantOperationError


class DocumentService:
    def __init__(self, qdrant_gateway: QdrantGateway, collection_service: CollectionService):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.qdrant = qdrant_gateway
        self.collection_service = collection_service
        self.document_repository = DocumentRepository()
        self.logger.info("Document Service initialized")

    async def get_documents(self, session: Session, user: User, collection_id: int) -> list[DocumentRead]:
        collection = await self.collection_service.get_collection(
            session=session,
            user=user,
            collection_id=collection_id
        )
        documents_db = self.document_repository.get_documents(session=session, collection_id=collection.id)

        return [
            DocumentRead(**document.model_dump())
            for document in documents_db
        ]

    async def get_document(self, session: Session, user: User, collection_id: int, document_id: int) -> DocumentRead:
        document_db = await self.__fetch_document(
            session=session,
            user=user,
            collection_id=collection_id,
            document_id=document_id
        )

        return DocumentRead(**document_db.model_dump())

    async def get_document_by_id(self, session: Session, user: User, document_id: int) -> DocumentRead:
        document_db = self.document_repository.get_document(session=session, document_id=document_id)

        if not document_db:
            raise DocumentNotFoundError(f"Document {document_id} not found")

        await self.collection_service.get_collection(
            session=session,
            user=user,
            collection_id=document_db.collection_id
        )

        return DocumentRead(**document_db.model_dump())


    async def add_document(
        self,
        session: Session,
        user: User,
        collection_id: int,
        document: DocumentCreate
    ) -> DocumentRead:
        collection = await self.collection_service.get_collection(
            session=session,
            user=user,
            collection_id=collection_id
        )
        document_db: DocumentDB = DocumentDB(**document.model_dump(), collection_id=collection.id)
        self.document_repository.add_document(session=session, document=document_db)

        session.commit()
        session.refresh(document_db)

        self.logger.info(f"Document {document_db.id} added to database")
        return DocumentRead(**document_db.model_dump())

    async def delete_document(self,
        session: Session,
        user: User,
        collection_id: int,
        document_id: int
    ):
        document_db = await self.__fetch_document(
            session=session,
            user=user,
            collection_id=collection_id,
            document_id=document_id
        )

        self.document_repository.delete_document(session=session, document=document_db, deleted_by=user.username)

        active_version = document_db.documents_versions[0] if document_db.documents_versions else None
        try:
            if active_version and active_version.qdrant_point_ids:
                await self.qdrant.delete_points(
                    collection_name=document_db.collection.qdrant_name,
                    point_ids=active_version.qdrant_point_ids
                )

            session.commit()
            self.logger.info(f"Document {document_id} marked as deleted in database")
            return True
        except Exception as err:
            session.rollback()
            self.logger.exception(f"Error deleting document {document_id} from Qdrant")
            raise QdrantOperationError(f"Error deleting document {document_id} from Qdrant") from err

    async def __fetch_document(self, session: Session, user: User, collection_id: int, document_id: int) -> DocumentDB:
        await self.collection_service.get_collection(
            session=session,
            user=user,
            collection_id=collection_id
        )
        document_db = self.document_repository.get_document(
            session=session,
            document_id=document_id
        )

        if not document_db or document_db.collection_id != collection_id:
            raise DocumentNotFoundError(f"Document {document_id} not found in collection {collection_id}")

        return document_db