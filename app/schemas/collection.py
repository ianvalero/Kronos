from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.enums import CollectionDistance


class CollectionQueryParams(BaseModel):
    gulax_name: str | None = None
    description: str | None = None
    roles: list[str] = []
    created_by: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class HNSWConfig(BaseModel):
    m: int = Field(gt=0, description="Maximum number of connections per node")
    ef_construct: int = Field(gt=0, description="Index quality during construction")


class CollectionCreate(BaseModel):
    gulax_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    roles: list[str] = Field(min_length=1)


class CollectionUpdate(BaseModel):
    gulax_name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    roles: list[str] | None = Field(default=None, min_length=1)


class CollectionCreateQdrant(BaseModel):
    name: str = Field(min_length=1)
    size: int = Field(gt=0, description="Number of dimensions for each vector")
    distance: CollectionDistance = Field(
        default=CollectionDistance.COSINE,
        description="Distance metric used to calculate similarity between vectors"
    )
    shard_number: int | None = Field(default=1, description="Number of shards used to partition the collection")
    replication_factor: int | None = Field(default=1, description="Number of replicas for high availability")
    on_disk_payload: bool | None = Field(default=True,description="Store payload metadata on disk instead of in RAM")
    hnsw_config: HNSWConfig | None = None

    model_config = ConfigDict(extra="forbid")


class CollectionVectors(BaseModel):
    dimension: int | dict[str, int]
    distance: CollectionDistance | dict[str, CollectionDistance]


class CollectionRead(BaseModel):
    id: int
    qdrant_name: str
    gulax_name: str
    description: str | None
    roles: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CollectionReadDetails(BaseModel):
    id: int
    qdrant_name: str
    gulax_name: str
    description: str | None
    roles: list[str]
    status: str
    points_count: int
    vectors: CollectionVectors
    created_at: datetime
    created_by: str
    updated_at: datetime | None
    updated_by: str | None
    deleted_at: datetime | None
    deleted_by: str | None

    model_config = ConfigDict(from_attributes=True)