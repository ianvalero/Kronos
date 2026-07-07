from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.database import get_session
import app.services as services
from app.models.user import UserDB
from app.models.collection import CollectionDB


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_redis_service(request: Request) -> services.RedisService:
    return request.app.state.redis_service

def get_qdrant_service(request: Request) -> services.QdrantService:
    return request.app.state.qdrant_service

def get_sql_service(request: Request) -> services.SqlService:
    return request.app.state.sql_service

def get_celery_service(request: Request) -> services.CeleryService:
    return request.app.state.celery_service

def get_collection_service(request: Request) -> services.CollectionService:
    return request.app.state.collection_service

def get_user_service(request: Request) -> services.UserService:
    return request.app.state.user_service

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UserDB:
    statement = select(UserDB).where(UserDB.id == token)
    user = session.exec(statement).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o usuario no encontrado"
        )

    return user

def require_admin(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permissions are required"
        )
    return current_user

def get_authorized_collection(
    collection_id: int,
    current_user: UserDB = Depends(get_current_user),
    session: Session = Depends(get_session),
    collection_service: services.CollectionService = Depends(get_collection_service),
) -> CollectionDB:
    collection_db = collection_service.collection_repository.get_collection(session, collection_id)
    if not collection_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    if current_user.is_admin:
        return collection_db

    user_group_ids = {group.id for group in current_user.groups}
    collection_group_ids = {group.id for group in collection_db.groups}

    if not collection_group_ids & user_group_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")

    return collection_db