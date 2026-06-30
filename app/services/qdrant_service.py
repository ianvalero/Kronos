import asyncio
import logging
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import VectorParams, Distance, HnswConfigDiff

from app.config.settings import settings
from app.schemas.collection import CollectionCreate

class QdrantService:
    def __init__(self):
        self.logger = logging.getLogger(f"app.{__name__}")

        self._qdrant_client = QdrantClient(url=settings.qdrant_url)
        self._qdrant_aclient = AsyncQdrantClient(url=settings.qdrant_url)

        self._index_cache: dict = {}
        self.logger.info("Qdrant Service initialized")

    async def get_collections(self) -> dict:
        self.logger.info("Getting collections")
        try:
            collections = await self._qdrant_aclient.get_collections()

            full_collections = await asyncio.gather(*[
                self.get_collection(collection.name)
                for collection in collections.collections
            ])

            return {
                "count": len(full_collections),
                "collections": full_collections
            }

        except Exception as e:
            self.logger.error("Error getting collections")
            self.logger.exception(e)
            raise

    async def get_collection(self, collection_name: str) -> dict:
        self.logger.info(f"Getting collection {collection_name}")
        try:
            collection = await self._qdrant_aclient.get_collection(collection_name)

            vectors = collection.config.params.vectors
            if hasattr(vectors, "size"):
                dimension = vectors.size
                distance = vectors.distance.value
            elif isinstance(vectors, dict):
                dimension = {key: value.size for key, value in vectors.items()}
                distance = {key: value.distance.value for key, value in vectors.items()}
            else:
                dimension = None
                distance = None

            return {
                "name": collection_name,
                "status": collection.status.value,
                "points_count": collection.points_count,
                "vectors": {
                    "dimension": dimension,
                    "distance": distance,
                }
            }

        except Exception as e:
            self.logger.error(f"Error getting collection {collection_name}")
            self.logger.exception(e)
            raise

    async def get_vector_store(self, collection_name: str) -> QdrantVectorStore:
        if not await self.collection_exists(collection_name):
            raise ValueError(f"Collection {collection_name} not exists")

        return QdrantVectorStore(
            client=self._qdrant_client,
            aclient=self._qdrant_aclient,
            collection_name=collection_name
        )

    async def collection_exists(self, collection_name: str) -> bool:
        return await self._qdrant_aclient.collection_exists(collection_name)

    async def create_collection(self, config: CollectionCreate) -> dict:
        self.logger.info(f"Creating collection {config.name}")

        if await self.collection_exists(config.name):
            self.logger.error(f"Collection {config.name} already exists")
            raise ValueError(f"Collection {config.name} already exists")

        vectors_config = VectorParams(
            size=config.size,
            distance=Distance(config.distance.value)
        )

        hnsw_config = None
        if config.hnsw_config:
            hnsw_config = HnswConfigDiff(
                m=config.hnsw_config.m,
                ef_construct=config.hnsw_config.ef_construct
            )

        try:
            await self._qdrant_aclient.create_collection(
                collection_name=config.name,
                vectors_config=vectors_config,
                shard_number=config.shard_number,
                replication_factor=config.replication_factor,
                on_disk_payload=config.on_disk_payload,
                hnsw_config=hnsw_config
            )
            self.logger.info(f"Collection {config.name} created")
        except Exception as err:
            self.logger.error(f"Error creating collection")
            self.logger.exception(err)
            raise Exception(f"Error creating collection: {err}")

        return await self.get_collection(config.name)

    async def delete_collection(self, collection_name: str):
        self.logger.info(f"Deleting collection {collection_name}")

        if not await self.collection_exists(collection_name):
            self.logger.error(f"Collection {collection_name} not exists")
            raise ValueError(f"Collection {collection_name} not exists")

        await self._qdrant_aclient.delete_collection(collection_name)
        self.logger.info(f"Collection {collection_name} deleted")

        return True

    async def delete_points(self, collection_name: str, point_ids: list[int]):
        self.logger.info(f"Deleting {len(point_ids)} points from {collection_name}")

        try:
            await self._qdrant_aclient.delete(
                collection_name=collection_name,
                points_selector=point_ids
            )
        except Exception as e:
            self.logger.error(f"Error deleting points from {collection_name}")
            self.logger.exception(e)
            raise

    async def close(self):
        try:
            await self._qdrant_aclient.close()
            self._qdrant_client.close()
        except Exception as e:
            self.logger.error("Error closing Qdrant clients")
            self.logger.exception(e)
            raise