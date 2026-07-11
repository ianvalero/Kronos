from typing import TYPE_CHECKING
from sqlalchemy import Column, ARRAY, String
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from app.models.document import DocumentDB


class CollectionDB(SQLModel, table=True):
    __tablename__ = "collections"

    id: int | None = Field(default=None, primary_key=True)
    qdrant_name: str = Field(unique=True, index=True)
    gulax_name: str
    description: str | None = Field(default=None)
    roles: list[str] = Field(sa_column=Column(ARRAY(String)))
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str
    deleted_at: datetime | None = None
    deleted_by: str | None = None

    documents: list["DocumentDB"] = Relationship(back_populates="collection")