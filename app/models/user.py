from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.collection import CollectionDB

class UserGroup(SQLModel, table=True):
    __tablename__ = "user_group"

    user_id: int | None = Field(default=None, foreign_key="users.id", primary_key=True)
    group_id: int | None = Field(default=None, foreign_key="groups.id", primary_key=True)


class GroupCollection(SQLModel, table=True):
    __tablename__ = "group_collection"

    group_id: int | None = Field(default=None, foreign_key="groups.id", primary_key=True)
    collection_id: int | None = Field(default=None, foreign_key="collections.id", primary_key=True)


class UserDB(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="roles.id")
    sso_id: str
    name: str
    email: str
    is_active: bool = Field(default=True)
    last_login: str | None = Field(default=None)

    groups: list["GroupDB"] = Relationship(back_populates="users", link_model=UserGroup)


class GroupDB(SQLModel, table=True):
    __tablename__ = "groups"

    id: int | None = Field(default=None, primary_key=True)
    sso_group_id: str
    name: str

    collections: list["CollectionDB"] = Relationship(back_populates="groups", link_model=GroupCollection)
    users: list["UserDB"] = Relationship(back_populates="groups", link_model=UserGroup)


class RoleDB(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = Field(default=None)