import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

from app.config.log import setup_logging
import app.services as services
import app.infrastructure as infrastructure
from app.routers import collection, document, auth

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

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(collection.router, prefix="/api/collections", tags=["collections"])
app.include_router(document.router, prefix="/api/documents", tags=["documents"])
