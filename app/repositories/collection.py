from typing import cast
from datetime import datetime
from sqlmodel import Session, select, func

from app.models.collection import CollectionDB
from app.schemas.collection import CollectionQueryParams
from app.repositories.sorting import sort_data
from app.enums import CollectionSortField


COLLECTION_SORT_COLUMNS = {
    CollectionSortField.ID: CollectionDB.id,
    CollectionSortField.DESCRIPTION: CollectionDB.description,
    CollectionSortField.GULAX_NAME: CollectionDB.gulax_name,
    CollectionSortField.ROLES: CollectionDB.roles,
    CollectionSortField.CREATED_AT: CollectionDB.created_at,
    CollectionSortField.CREATED_BY: CollectionDB.created_by,
}

class CollectionRepository:
    def get_collections(
        self,
        session: Session,
        roles: list[str],
        params: CollectionQueryParams,
        is_admin: bool = False,
    ) -> tuple[list[CollectionDB], int]:
        if not is_admin and not roles:
            return [], 0

        where_conditions = [
            *self.__base_conditions(roles=roles, is_admin=is_admin),
            *self.__generate_filters(filters=params)
        ]

        collections_statement = select(CollectionDB).where(*where_conditions)
        collections_statement = sort_data(
            statement=collections_statement,
            sort_column=COLLECTION_SORT_COLUMNS[params.sort_by],
            direction=params.sort_order,
            tie_breaker=CollectionDB.id,
        )
        collections_statement= collections_statement.offset(params.offset).limit(params.limit)

        total_statement = (
            select(func.count())
            .select_from(CollectionDB)
            .where(*where_conditions)
        )

        collections = cast(list[CollectionDB], session.exec(collections_statement).all())
        total = cast(int, session.exec(total_statement).one())
        return collections, total

    def get_collection_ids(self, session: Session, roles: list[str], is_admin: bool = False) -> list[int]:
        if not is_admin and not roles:
            return []

        where_conditions = [*self.__base_conditions(roles=roles, is_admin=is_admin),]

        statement = select(CollectionDB.id).where(*where_conditions)
        return list(session.exec(statement).all())

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

    def __base_conditions(self, roles: list[str], is_admin: bool) -> list:
        where_conditions = [CollectionDB.deleted_at.is_(None)]
        if not is_admin:
            where_conditions.append(CollectionDB.roles.overlap(roles))
        return where_conditions

    def __generate_filters(self, filters: CollectionQueryParams | None = None) -> list:
        where_conditions = []

        if filters:
            if filters.gulax_name:
                where_conditions.append(CollectionDB.gulax_name.ilike(f"%{filters.gulax_name}%"))
            if filters.description:
                where_conditions.append(CollectionDB.description.ilike(f"%{filters.description}%"))
            if filters.roles:
                where_conditions.append(CollectionDB.roles.overlap(filters.roles))
            if filters.created_by:
                where_conditions.append(CollectionDB.created_by == filters.created_by)
            if filters.created_at_from:
                where_conditions.append(CollectionDB.created_at >= filters.created_at_from)
            if filters.created_at_to:
                where_conditions.append(CollectionDB.created_at <= filters.created_at_to)

        return where_conditions