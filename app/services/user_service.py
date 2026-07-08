import logging
import secrets
from sqlmodel import Session

from app.repositories.user import UserRepository
from app.schemas.user import UserSSO, UserLoginResponse

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
        session.refresh(user)

        return UserLoginResponse(
            id=user_db.id,
            username=user_db.username,
            api_key=new_api_key
        )