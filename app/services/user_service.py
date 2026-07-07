import logging
from sqlmodel import Session

from app.repositories.user import UserRepository
from app.models.user import UserDB


class UserService:
    DEFAULT_ROLE_ID = 2

    def __init__(self):
        self.logger = logging.getLogger(f"app.{__name__}")
        self.user_repository = UserRepository()
        self.logger.info("User Service initialized")

    def sync_user_from_sso(
            self,
            session: Session,
            sso_id: str,
            name: str,
            email: str,
            sso_group_ids: list[str],
    ) -> UserDB:
        user = self.user_repository.get_by_sso_id(session, sso_id)

        if not user:
            user = self.user_repository.create_user(
                session=session,
                sso_id=sso_id,
                name=name,
                email=email,
                default_role_id=self.DEFAULT_ROLE_ID,
            )
            self.logger.info(f"SSO User created: {sso_id}")
        else:
            user.name = name
            user.email = email

        groups = self.user_repository.get_by_sso_group_ids(session, sso_group_ids)
        self.user_repository.sync_user_groups(session, user, groups)

        session.commit()
        session.refresh(user)
        return user