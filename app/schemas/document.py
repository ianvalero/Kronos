from datetime import datetime
from sqlmodel import SQLModel
from pydantic import ConfigDict, BaseModel, Field

from app.schemas.document_version import DocumentVersionRead
from app.schemas.collection import CollectionRead


class DocumentQueryParams(BaseModel):
    collection_id: int | None = Field(default=None, gt=0)
    description: str | None = None
    roles: list[str] = []
    created_by: str | None = None
    created_at_from: datetime | None = None
    created_at_to: datetime | None = None
    include_deleted: bool = False
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

class DocumentRead(SQLModel):
    id: int
    description: str
    collection: CollectionRead
    created_at: datetime
    created_by: str
    updated_at: datetime | None = None
    updated_by: str | None = None
    deleted_at: datetime | None = None
    deleted_by: str | None = None

    documents_versions: list[DocumentVersionRead] = list()

    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(SQLModel):
    description: str

class DocumentUpdate(SQLModel):
    description: str