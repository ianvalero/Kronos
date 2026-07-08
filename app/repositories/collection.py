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
        collection = CollectionDB(**collection.model_dump())
        session.add(collection)
        session.flush()
        return collection

    def delete_collection(self, session: Session, collection_id: int) -> bool:
        collection = self.get_collection(session, collection_id)
        if not collection:
            return False

        collection.deleted_at = datetime.now()
        session.flush()
        return True