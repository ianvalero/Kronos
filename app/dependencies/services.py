from fastapi import Request
import app.services as services

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