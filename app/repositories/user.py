import hashlib
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlmodel import Session, select

from app.models.user import UserDB
from app.schemas.user import UserSSO


class UserRepository:
    def get_by_sso_id(self, session: Session, sso_id: str) -> UserDB | None:
        statement = (
            select(UserDB)
            .where(UserDB.sso_id == sso_id)
        )
        return session.exec(statement).first()

    def get_by_api_key(self, session: Session, raw_api_key: str) -> UserDB | None:
        api_key_hash = hashlib.sha256(raw_api_key.encode()).hexdigest()
        statement = (
            select(UserDB)
            .where(UserDB.api_key_hash == api_key_hash)
        )
        return session.exec(statement).first()

    def update_or_create_user(self, session: Session, user: UserSSO) -> UserDB:
        user = self.get_by_sso_id(session, user.sso_id)
        if not user:
            user = UserDB(
                sso_id=user.sso_id,
                username=user.username,
                name=user.name,
                email=user.email,
                roles=user.roles
            )
            session.add(user)
        else:
            user.username = user.username
            user.name = user.name
            user.email = user.email
            user.roles = user.roles
            user.is_active = True

        session.flush()
        return user

    def set_api_key(self, session: Session, user: UserDB, api_key: str) -> None:
        user.api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        self.update_api_key_expiration_date(session, user)

    def update_api_key_expiration_date(self, session: Session, user: UserDB) -> None:
        user.api_key_expires_at = datetime.now(timezone.utc) + relativedelta(months=3)
        session.add(user)
        session.flush()