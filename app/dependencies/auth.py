from fastapi import Header, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.services.user_service import UserService
from app.dependencies.services import get_user_service
from app.schemas.user import User
from app.models.user import UserDB

def get_current_user(
    x_api_key: str = Header(...),
    session: Session = Depends(get_session),
    user_service: UserService = Depends(get_user_service),
) -> User:
    user = user_service.user_repository.get_by_api_key(session, x_api_key)

    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive API key")

    user_service.user_repository.extend_api_key_expiry(session, user)
    return User(
        username=user.username,
        email=user.email,
        name=user.name,
        roles=user.roles,
        is_admin=user.is_admin
    )

def require_admin(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if "ROLE_ADMIN" not in current_user.roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Administrator permissions are required")
    return current_user