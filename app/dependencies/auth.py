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
    return user_service.get_current_user(session, x_api_key)

def require_admin(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if current_user.is_admin not in current_user.roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Administrator permissions are required")
    return current_user