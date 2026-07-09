from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from app.models.document_version import DocumentVersionDB
    from app.models.collection import CollectionDB

class DocumentDB(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    collection_id: int = Field(foreign_key="collections.id", index=True)
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None
    deleted_by: str | None = None

    collection: "CollectionDB" = Relationship(back_populates="documents")
    documents_versions: list["DocumentVersionDB"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"order_by": "DocumentVersionDB.id.desc()"}
    )