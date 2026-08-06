from enum import Enum


class CollectionDistance(str, Enum):
    COSINE = "Cosine"
    EUCLID = "Euclid"
    DOT = "Dot"

class DocumentVersionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"