from typing import cast
from datetime import datetime
from sqlmodel import Session, select, func

from app.models.collection import CollectionDB

class CollectionRepository:
    def get_collections(self, session: Session, offset: int = 0, limit: int = 100) -> tuple[list[CollectionDB], int]:
        where_conditions = (
            CollectionDB.deleted_at.is_(None),
        )

        collections = (
            select(CollectionDB)
            .where(*where_conditions)
            .order_by(CollectionDB.id)
            .offset(offset)
            .limit(limit)
        )

        total = (
            select(func.count())
            .select_from(CollectionDB)
            .where(*where_conditions)
        )

        collections = cast(list[CollectionDB], session.exec(collections).all())
        total = cast(int, session.exec(total).one())
        return collections, total

    def get_collections_by_roles(
        self,
        session: Session,
        roles: list[str],
        offset: int = 0,
        limit: int = 100
    ) -> tuple[list[CollectionDB], int]:
        if not roles:
            return [], 0

        where_conditions = (
            CollectionDB.deleted_at.is_(None),
            CollectionDB.roles.overlap(roles),
        )

        collections = (
            select(CollectionDB)
            .where(*where_conditions)
            .distinct()
            .order_by(CollectionDB.id)
            .offset(offset)
            .limit(limit)
        )

        total = (
            select(func.count(func.distinct(CollectionDB.id)))
            .select_from(CollectionDB)
            .where(*where_conditions)
        )

        collections = cast(list[CollectionDB], session.exec(collections).all())
        total = cast(int, session.exec(total).one())
        return collections, total

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

    def update_collection(self, session: Session, collection: CollectionDB) -> CollectionDB:
        collection.updated_at = datetime.now()
        session.add(collection)
        session.flush()
        return collection

    def delete_collection(self, session: Session, collection: CollectionDB) -> bool:
        collection.deleted_at = datetime.now()
        session.flush()
        return True