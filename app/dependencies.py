from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.database import get_session
import app.services as services
from app.models.user import UserDB


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

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UserDB:
    statement = select(UserDB).where(UserDB.id == token)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o usuario no encontrado"
        )

    return user