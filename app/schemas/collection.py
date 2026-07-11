from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


class Distance(str, Enum):
    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"


class HNSWConfig(BaseModel):
    m: int = Field(gt=0, description="Maximum number of connections per node")
    ef_construct: int = Field(gt=0, description="Index quality during construction")


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    roles: list[str] = Field(min_length=1)


class CollectionCreateQdrant(BaseModel):
    name: str = Field(min_length=1)
    size: int = Field(gt=0, description="Number of dimensions for each vector")
    distance: Distance = Field(default=Distance.COSINE, description="Distance metric used to calculate similarity between vectors")
    shard_number: int | None = Field(default=1, description="Number of shards used to partition the collection")
    replication_factor: int | None = Field(default=1, description="Number of replicas for high availability")
    on_disk_payload: bool | None = Field(default=True,description="Store payload metadata on disk instead of in RAM")
    hnsw_config: HNSWConfig | None = None

    model_config = ConfigDict(extra="forbid")


class CollectionVectors(BaseModel):
    dimension: int | dict[str, int]
    distance: Distance | dict[str, Distance]


class CollectionRead(BaseModel):
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
    deleted_at: datetime | None
    deleted_by: str | None


class CollectionsResponse(BaseModel):
    count: int
    collections: list[CollectionRead]