from datetime import datetime
from sqlmodel import SQLModel
from pydantic import ConfigDict

from app.schemas.document_version import DocumentVersion


class DocumentRead(SQLModel):
    id: int
    collection_id: int
    description: str
    created_at: datetime
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    documents_versions: list[DocumentVersion] = list()

    model_config = ConfigDict(from_attributes=True)


class DocumentCreate(SQLModel):
    description: str