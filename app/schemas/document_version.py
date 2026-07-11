from datetime import datetime
from sqlmodel import SQLModel
from typing import Any


class DocumentVersion(SQLModel):
    id: int
    document_id: int
    filename: str
    original_filename: str
    uploaded_by: str
    uploaded_at: datetime
    task_id: str | None = None
    error_message: str | None
    status: str

class DocumentVersionDetail(DocumentVersion):
    file_path: str
    file_size: int
    mime_type: str
    qdrant_point_ids: list[str] | None
    attempts: int


class DocumentVersionTaskRead(SQLModel):
    task_id: str
    status: str
    result: Any | None = None