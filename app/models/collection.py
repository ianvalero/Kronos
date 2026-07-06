from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from app.models.user import GroupCollection

if TYPE_CHECKING:
    from app.models.user import GroupDB

class CollectionDB(SQLModel, table=True):
    __tablename__ = "collections"

    id: int | None = Field(default=None, primary_key=True)
    qdrant_name: str = Field(unique=True, index=True)
    gulax_name: str
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    groups: list["GroupDB"] = Relationship(
        back_populates="collections",
        link_model=GroupCollection
    )