from fastapi import Request

from app.services.qdrant_service import QdrantService
from app.services.redis_service import RedisService
from app.services.sql_service import SqlService


def get_redis_service(request: Request) -> RedisService:
    return request.app.state.redis_service

def get_qdrant_service(request: Request) -> QdrantService:
    return request.app.state.qdrant_service

def get_sql_service(request: Request) -> SqlService:
    return request.app.state.sql_service