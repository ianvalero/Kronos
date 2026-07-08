from datetime import datetime
from sqlmodel import Session, select

from app.models.collection import CollectionDB
from app.models.user import GroupCollection

class CollectionRepository:
    def get_collections(self, session: Session) -> list[CollectionDB]:
        statement = (
            select(CollectionDB)
            .where(CollectionDB.deleted_at.is_(None))
        )
        return session.exec(statement).all()

    #TODO Revisar si esto es necesario
    def get_collections_by_groups(self, session: Session, group_ids: list[int]) -> list[CollectionDB]:
        if not group_ids:
            return []

        statement = (
            select(CollectionDB)
            .join(GroupCollection, GroupCollection.collection_id == CollectionDB.id)
            .where(
                CollectionDB.deleted_at.is_(None),
                GroupCollection.group_id.in_(group_ids),
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

    def create_collection(self, session: Session, collection: CollectionDB, group_id: int) -> CollectionDB:
        collection = CollectionDB(**collection.model_dump())
        session.add(collection)
        session.flush()

        self.__add_group_collection(session, group_id=group_id, collection_id=collection.id)
        session.flush()
        return collection

    def delete_collection(self, session: Session, collection_id: int) -> bool:
        collection = self.get_collection(session, collection_id)
        if not collection:
            return False

        collection.deleted_at = datetime.now()
        session.flush()
        return True

    def __add_group_collection(self, session: Session, group_id: int, collection_id: int):
        group_collection = GroupCollection(
            collection_id=collection_id,
            group_id=group_id
        )
        session.add(group_collection)
        return True