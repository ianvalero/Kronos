from typing import TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from app.schemas.document_version import DocumentVersionRead

class DocumentRead(SQLModel):
    id: int
    collection_id: int
    description: str
    created_at: datetime
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    documents_versions: list["DocumentVersionRead"] = list()


class DocumentCreate(SQLModel):
    description: str


class DocumentDelete(SQLModel):
    deleted_by: str