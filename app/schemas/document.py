from datetime import datetime
from sqlmodel import SQLModel

class DocumentRead(SQLModel):
    id: int
    team: str
    collection: str
    description: str
    created_at: datetime
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    documents_versions: list["DocumentVersionRead"] = list()


class DocumentVersionRead(SQLModel):
    id: int
    document_id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_at: datetime
    task_id: str | None = None
    qdrant_point_ids: list[int] | None
    attempts: int
    error_message: str | None
    status: str


class DocumentVersionTaskRead(SQLModel):
    task_id: int
    status: int
    result: str | None


class DocumentCreate(SQLModel):
    team: str
    collection: str
    description: str


class DocumentVersionCreate(SQLModel):
    saved_file_path: str
    filename: str
    uploaded_by: str
    file_size: int
    mime_type: str


class DocumentDelete(SQLModel):
    deleted_by: str
