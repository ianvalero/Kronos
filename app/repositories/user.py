from sqlmodel import Session, select

from app.models.user import UserDB, GroupDB, UserGroup

class UserRepository:
    def get_by_sso_id(self, session: Session, sso_id: str) -> UserDB | None:
        statement = (
            select(UserDB)
            .where(UserDB.sso_id == sso_id)
        )
        return session.exec(statement).first()

    def get_by_sso_group_ids(self, session: Session, sso_group_ids: list[str]) -> list[GroupDB]:
        if not sso_group_ids:
            return []

        statement = (
            select(GroupDB)
            .where(GroupDB.sso_group_id.in_(sso_group_ids))
        )
        return session.exec(statement).all()

    def create_user(self, session: Session, sso_id: str, name: str, email: str, default_role_id: int) -> UserDB:
        user = UserDB(sso_id=sso_id, name=name, email=email, role_id=default_role_id)
        session.add(user)
        session.flush()
        return user

    def sync_user_groups(self, session: Session, user: UserDB, groups: list[GroupDB]) -> None:
        current_group_ids = {g.id for g in user.groups}
        target_group_ids = {g.id for g in groups}

        for group_id in target_group_ids - current_group_ids:
            session.add(UserGroup(user_id=user.id, group_id=group_id))

        for group_id in current_group_ids - target_group_ids:
            statement = select(UserGroup).where(
                UserGroup.user_id == user.id, UserGroup.group_id == group_id
            )
            link = session.exec(statement).first()
            if link:
                session.delete(link)

        session.flush()