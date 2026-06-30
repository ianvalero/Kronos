from pydantic import BaseModel, Field, ConfigDict
from typing import List, Union, Literal, Optional

from enum import Enum

class Distance(str, Enum):
    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"


class CollectionVectors(BaseModel):
    dimension: Union[int, dict[str, int]]
    distance: Union[Distance, dict[str, Distance]]


class Collection(BaseModel):
    name: str
    status: str
    points_count: int
    vectors: CollectionVectors


class CollectionsResponse(BaseModel):
    count: int
    collections: List[Collection]


class HNSWConfig(BaseModel):
    m: int = 16                                                 # Número de conexiones por nodo
    ef_construct: int = 200                                     # Calidad del índice al construirlo


class CollectionCreate(BaseModel):
    name: str
    size: int = Field(1536, gt=0)                               # Número de dimensiones de cada vector
    distance: Distance = Distance.COSINE                        # Define como se calcula la similitud entre vectores

    shard_number: Optional[int] = 1                             # Divide la colección en particiones
    replication_factor: Optional[int] = 1                       # Duplica datos para alta disponibilidad
    on_disk_payload: Optional[bool] = True                      # Guardar metadata en disco en lugar de RAM

    hnsw_config: Optional[HNSWConfig] = None

    model_config = ConfigDict(extra="forbid")