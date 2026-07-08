import logging

from app.exceptions import AppException
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

from app.config.log import setup_logging
from app.routers import collection, document, auth
import app.services as services
import app.infrastructure as infrastructure

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(f"app.{__name__}")
    logger.info("Starting application")

    LlamaIndexInstrumentor().instrument()

    app.state.qdrant_gateway = infrastructure.QdrantGateway()
    app.state.redis_client = infrastructure.RedisClient()
    app.state.celery_client = infrastructure.CeleryClient()
    app.state.collection_service = services.CollectionService()
    app.state.user_service = services.UserService()

    yield
    await app.state.qdrant_gateway.close()
    app.state.redis_client.close()

    logger.info("Stopping application")

app = FastAPI(
    title="Qdrant Management",
    description="API for Qdrant Management",
    version="0.1.0",
    lifespan=lifespan
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(collection.router, prefix="/api/collections", tags=["collections"])
app.include_router(document.router, prefix="/api/documents", tags=["documents"])
