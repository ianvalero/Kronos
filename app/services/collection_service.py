import logging
import uuid

from sqlmodel import Session

from app.config.settings import settings
from app.repositories.collection import CollectionRepository
from app.models.collection import CollectionDB
from app.infrastructure.qdrant_gateway import QdrantGateway
import app.schemas.collection as CollectionSchema
from app.schemas.user import User
from app.exceptions import CollectionPermissionError, CollectionNotFoundError


class CollectionService:
    def __init__(self, qdrant_gateway: QdrantGateway):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.qdrant = qdrant_gateway
        self.collection_repository = CollectionRepository()
        self.logger.info("Collection Service initialized")

    async def get_collections(
        self,
        session: Session,
        user: User,
        params: CollectionSchema.CollectionQueryParams
    ) -> tuple[list[CollectionSchema.CollectionReadDetails], int]:
        collections_db, total = self.collection_repository.get_collections(
            session=session,
            roles=user.roles,
            params=params,
            is_admin=user.is_admin
        )

        collections_qdrant = await self.qdrant.get_collections(
            collection_names=[collection.qdrant_name for collection in collections_db]
        )
        qdrant_map = {collection["name"]: collection for collection in collections_qdrant["collections"]}

        collections_read = [
            self.__create_collection_read(collection_db, qdrant_map.get(collection_db.qdrant_name, {}))
            for collection_db in collections_db
        ]
        return collections_read, total

    async def get_collection_ids(self, session: Session, user: User) -> list[int]:
        return self.collection_repository.get_collection_ids(
            session=session,
            roles=user.roles,
            is_admin=user.is_admin
        )

    async def get_collection(self, session: Session, user: User, collection_id: int) -> CollectionSchema.CollectionReadDetails:
        collection_db = self.__get_db_collection(session=session, user=user, collection_id=collection_id)
        collection_qdrant = await self.qdrant.get_collection(collection_name=collection_db.qdrant_name)
        return self.__create_collection_read(collection_db, collection_qdrant)

    async def check_access(self, session: Session, user: User, collection_id: int) -> None:
        self.__get_db_collection(session=session, user=user, collection_id=collection_id)

    async def create_collection(
        self,
        session: Session,
        user: User,
        new_collection: CollectionSchema.CollectionCreate
    ) -> CollectionSchema.CollectionReadDetails:
        if not user.is_admin and not set(new_collection.roles).issubset(set(user.roles)):
            raise CollectionPermissionError("User does not have permission to create a collection in this group.")

        qdrant_name = f"col_{new_collection.gulax_name}_{uuid.uuid4().hex}"

        collection_db = CollectionDB(
            qdrant_name=qdrant_name,
            gulax_name=new_collection.gulax_name,
            description=new_collection.description,
            roles=new_collection.roles,
            created_by=user.username
        )
        self.collection_repository.create_collection(session=session, collection=collection_db)

        qdrant_config = CollectionSchema.CollectionCreateQdrant(
            name=qdrant_name,
            size=settings.qdrant.size,
            distance=settings.qdrant.distance,
            shard_number=settings.qdrant.shard_number,
            replication_factor=settings.qdrant.replication_factor,
            on_disk_payload=settings.qdrant.on_disk_payload,
            hnsw_config=CollectionSchema.HNSWConfig(
                m=settings.qdrant.node_conexions_number,
                ef_construct=settings.qdrant.ef_construct
            ),
        )
        collection_qdrant = await self.qdrant.create_collection(config=qdrant_config)

        session.commit()
        session.refresh(collection_db)

        self.logger.info(
            f"Colección {new_collection.gulax_name} creada con éxito "
            f"| SQL ID: {collection_db.id} "
            f"| Qdrant: {qdrant_name}"
        )
        return self.__create_collection_read(collection_db, collection_qdrant)

    async def update_collection(
        self,
        session: Session,
        user: User,
        collection_id: int,
        data: CollectionSchema.CollectionUpdate
    ) -> CollectionSchema.CollectionReadDetails:
        collection_db = self.__get_db_collection(session=session, user=user, collection_id=collection_id)

        update_data = data.model_dump(exclude_unset=True)
        if "roles" in update_data and not user.is_admin and not set(update_data["roles"]).issubset(set(user.roles)):
            raise CollectionPermissionError("User does not have permission to assign these roles.")

        for field, value in update_data.items():
            setattr(collection_db, field, value)
        collection_db.updated_by = user.username

        self.collection_repository.update_collection(session=session, collection=collection_db)
        session.commit()
        session.refresh(collection_db)

        collection_qdrant = await self.qdrant.get_collection(collection_name=collection_db.qdrant_name)

        self.logger.info(
            f"Colección {collection_db.gulax_name} modificada con éxito "
            f"| SQL ID: {collection_db.id} "
            f"| Qdrant: {collection_db.qdrant_name}"
        )
        return self.__create_collection_read(collection_db, collection_qdrant)

    async def delete_collection(self, session: Session, user: User, collection_id: int) -> bool:
        collection_db = self.__get_db_collection(session=session, user=user, collection_id=collection_id)

        collection_db.deleted_by = user.username
        self.collection_repository.delete_collection(session=session, collection=collection_db)

        await self.qdrant.delete_collection(collection_name=collection_db.qdrant_name)
        session.commit()

        self.logger.info(
            f"Colección {collection_db.gulax_name} eliminada con éxito "
            f"| SQL ID: {collection_db.id} "
            f"| Qdrant: {collection_db.qdrant_name}"
        )
        return True

    def __get_db_collection(self, session: Session, user: User, collection_id: int) -> CollectionDB:
        collection_db = self.collection_repository.get_collection(session=session, collection_id=collection_id)

        if not collection_db:
            raise CollectionNotFoundError(f"Collection with ID {collection_id} not found.")
        elif not user.is_admin and not (set(collection_db.roles) & set(user.roles)):
            raise CollectionPermissionError("User does not have permission to access this collection.")

        return collection_db

    @staticmethod
    def __create_collection_read(collection_db: CollectionDB, collection_qdrant: dict) -> CollectionSchema.CollectionReadDetails:
        return CollectionSchema.CollectionReadDetails(
            id=collection_db.id,
            qdrant_name=collection_db.qdrant_name,
            gulax_name=collection_db.gulax_name,
            description=collection_db.description,
            roles=collection_db.roles,
            status=collection_qdrant.get('status', 'unknown'),
            vectors=collection_qdrant.get('vectors', None),
            created_at=collection_db.created_at,
            created_by=collection_db.created_by,
            updated_at=collection_db.updated_at,
            updated_by=collection_db.updated_by,
            deleted_at=collection_db.deleted_at,
            deleted_by=collection_db.deleted_by
        )