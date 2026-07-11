from datetime import datetime
from sqlmodel import Session, select

from app.models.collection import CollectionDB

class CollectionRepository:
    def get_collections(self, session: Session) -> list[CollectionDB]:
        statement = (
            select(CollectionDB)
            .where(CollectionDB.deleted_at.is_(None))
        )
        return session.exec(statement).all()

    def get_collections_by_roles(self, session: Session, roles: list[str]) -> list[CollectionDB]:
        if not roles:
            return []

        statement = (
            select(CollectionDB)
            .where(
                CollectionDB.deleted_at.is_(None),
                CollectionDB.roles.overlap(roles),
            )
            .distinct()
        )
        return session.exec(statement).all()

    def get_collection(self, session: Session, collection_id: int) -> CollectionDB | None:
        statement = (
            select(CollectionDB)
            .where(
                CollectionDB.id == collection_id,
                CollectionDB.deleted_at.is_(None),
            )
        )
        return session.exec(statement).first()

    def create_collection(self, session: Session, collection: CollectionDB) -> CollectionDB:
        session.add(collection)
        session.flush()
        return collection

    def delete_collection(self, session: Session, collection: CollectionDB, deleted_by: str) -> bool:
        collection.deleted_at = datetime.now()
        collection.deleted_by = deleted_by
        session.flush()
        return True