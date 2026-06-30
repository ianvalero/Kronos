from sqlalchemy import Integer, ARRAY, Column
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class DocumentDB(SQLModel, table=True):
    __tablename__ = "documents"
    id: int | None = Field(default=None, primary_key=True)
    team: str = Field(index=True)
    collection: str = Field(index=True)
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None
    deleted_by: str | None = None
    documents_versions: list["DocumentVersionDB"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"order_by": "DocumentVersionDB.id.desc()"}
    )


class DocumentVersionDB(SQLModel, table=True):
    __tablename__ = "documents_versions"
    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", index=True)
    document: DocumentDB = Relationship(back_populates="documents_versions")
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.now)
    task_id: str | None = Field(default=None, index=True)
    qdrant_point_ids: list[int] | None = Field(
        default=None,
        sa_column=Column(ARRAY(Integer))
    )
    attempts: int = 0
    error_message: str | None = None
    status: str = "pending"