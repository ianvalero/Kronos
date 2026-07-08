import logging
import uuid

from sqlmodel import Session

from app.config.settings import settings
from app.repositories.collection import CollectionRepository
from app.models.collection import CollectionDB
from app.infrastructure.qdrant_gateway import QdrantGateway
from app.schemas.collection import CollectionCreate, CollectionCreateQdrant, HNSWConfig
from app.schemas.collection import CollectionRead, CollectionsResponse
from app.schemas.user import User
from app.exceptions import CollectionPermissionError


class CollectionService:
    def __init__(self):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.collection_repository = CollectionRepository()
        self.logger.info("Collection Service initialized")

    async def get_collections(
        self,
        session: Session,
        qdrant: QdrantGateway,
        user: User
    ) -> CollectionsResponse:
        try:
            if user.is_admin:
                collections_db = self.collection_repository.get_collections(session=session)
            else:
                collections_db = self.collection_repository.get_collections_by_roles(session, user.roles)

            collections_qdrant = await qdrant.get_collections(
                collection_names=[collection.qdrant_name for collection in collections_db]
            )

            qdrant_map = {collection["name"]: collection for collection in collections_qdrant["collections"]}
        except Exception:
            self.logger.exception("Error fetching collections from Qdrant")
            raise

        collections_read = [
            self.__create_collection_read(collection_db, qdrant_map.get(collection_db.qdrant_name, {}))
            for collection_db in collections_db
        ]

        return CollectionsResponse(count=len(collections_read), collections=collections_read)

    async def get_collection(
        self,
        session: Session,
        qdrant: QdrantGateway,
        user: User,
        collection_id: int
    ) -> CollectionRead:
        collection_db = self.collection_repository.get_collection(session=session, collection_id=collection_id)

        if not collection_db:
            raise ValueError(f"Collection with ID {collection_id} not found.")
        elif "ROLE_ADMIN" not in user.roles and not (set(collection_db.roles) & set(user.roles)):
            raise PermissionError("You do not have permission to access this collection.")

        try:
            collection_qdrant = await qdrant.get_collection(collection_name=collection_db.qdrant_name)
        except Exception:
            self.logger.exception(f"Error fetching collection {collection_db.qdrant_name} from Qdrant")
            raise

        return self.__create_collection_read(collection_db, collection_qdrant)

    async def create_collection(
        self,
        session: Session,
        qdrant: QdrantGateway,
        user: User,
        new_collection: CollectionCreate
    ) -> CollectionRead:
        if not user.is_admin and not set(new_collection.roles).issubset(set(user.roles)):
            raise CollectionPermissionError("User does not have permission to create a collection in this group.")

        qdrant_name = f"col_{new_collection.name}_{uuid.uuid4().hex}"

        try:
            collection_db = CollectionDB(
                qdrant_name=qdrant_name,
                gulax_name=new_collection.name,
                description=new_collection.description,
                roles=new_collection.roles
            )
            self.collection_repository.create_collection(session=session, collection=collection_db)

            qdrant_config = CollectionCreateQdrant(
                name=qdrant_name,
                size=settings.qdrant.size,
                distance=settings.qdrant.distance,
                shard_number=settings.qdrant.shard_number,
                replication_factor=settings.qdrant.replication_factor,
                on_disk_payload=settings.qdrant.on_disk_payload,
                hnsw_config=HNSWConfig(
                    m=settings.qdrant.node_conexions_number,
                    ef_construct=settings.qdrant.ef_construct
                ),
            )
            collection_qdrant = await qdrant.create_collection(config=qdrant_config)

            session.commit()
            session.refresh(collection_db)

            self.logger.info(
                f"Colección {new_collection.name} creada con éxito "
                f"| SQL ID: {collection_db.id} "
                f"| Qdrant: {qdrant_name}"
            )
            return self.__create_collection_read(collection_db, collection_qdrant)

        except Exception:
            session.rollback()
            self.logger.exception(f"Error creating collection {new_collection.name}")
            raise

    async def delete_collection(self, session: Session, qdrant: QdrantGateway, user: User, collection_id: int) -> bool:
        collection_db = self.collection_repository.get_collection(session=session, collection_id=collection_id)
        if not collection_db:
            raise ValueError(f"Collection with ID {collection_id} not found.")

        if not user.is_admin and not set(collection_db.roles).issubset(set(user.roles)):
            raise CollectionPermissionError("User does not have permission to delete a collection in this group.")

        try:
            self.collection_repository.delete_collection(session=session, collection_id=collection_id)
            await qdrant.delete_collection(collection_name=collection_db.qdrant_name)

            session.commit()

            self.logger.info(
                f"Colección {collection_db.gulax_name} eliminada con éxito "
                f"| SQL ID: {collection_db.id} "
                f"| Qdrant: {collection_db.qdrant_name}"
            )
            return True

        except Exception:
            session.rollback()
            self.logger.exception(f"Error deleting collection {collection_id}")
            raise

    def __create_collection_read(self, collection_db: CollectionDB, collection_qdrant: dict) -> CollectionRead:
        return CollectionRead(
            id=collection_db.id,
            qdrant_name=collection_db.qdrant_name,
            gulax_name=collection_db.gulax_name,
            description=collection_db.description,
            created_at=collection_db.created_at,
            status=collection_qdrant["status"],
            points_count=collection_qdrant["points_count"],
            vectors=collection_qdrant["vectors"]
        )