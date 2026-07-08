import logging
import secrets
from sqlmodel import Session

from app.repositories.user import UserRepository
from app.schemas.user import UserSSO, UserLoginResponse, User
from app.exceptions import InvalidApiKeyError

class UserService:
    def __init__(self):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.user_repository = UserRepository()
        self.logger.info("User Service initialized")

    def authenticate_sso_user(self, session: Session, user: UserSSO) -> str:
        user_db = self.user_repository.update_or_create_user(session, user)
        new_api_key = secrets.token_urlsafe(32)

        self.user_repository.set_api_key(session, user_db, new_api_key)

        session.commit()
        session.refresh(user_db)

        return UserLoginResponse(
            id=user_db.id,
            username=user_db.username,
            api_key=new_api_key
        )

    def get_current_user(self, session: Session, raw_api_key: str) -> User:
        user_db = self.user_repository.get_by_api_key(session, raw_api_key)

        if not user_db or not user_db.is_active:
            raise InvalidApiKeyError("Invalid or inactive API key")

        self.user_repository.update_api_key_expiration_date(session, user_db)
        return User(
            username=user_db.username,
            email=user_db.email,
            name=user_db.name,
            roles=user_db.roles,
            is_admin=user_db.is_admin,
        )