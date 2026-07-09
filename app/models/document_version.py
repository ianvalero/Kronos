from sqlalchemy import ARRAY, Column, String
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from app.models.document import DocumentDB

class DocumentVersionDB(SQLModel, table=True):
    __tablename__ = "documents_versions"

    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", index=True)
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    task_id: str | None = Field(default=None, index=True)
    qdrant_point_ids: list[str] | None = Field(
        default=None,
        sa_column=Column(ARRAY(String))
    )
    attempts: int = 0
    error_message: str | None = None
    status: str = "pending"

    document: DocumentDB = Relationship(back_populates="documents_versions")