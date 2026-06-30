import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from sqlmodel import SQLModel

from app.config.log import setup_logging
import app.services as services
from app.routers import collection, document
from app.database import engine

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger(f"app.{__name__}")
    logger.info("Starting application")

    LlamaIndexInstrumentor().instrument()
    SQLModel.metadata.create_all(engine)

    app.state.qdrant_service = services.QdrantService()
    app.state.sql_service = services.SqlService()
    app.state.redis_service = services.RedisService()
    app.state.celery_service = services.CeleryService()

    yield
    await app.state.qdrant_service.close()
    app.state.redis_service.close()

    logger.info("Stopping application")

app = FastAPI(
    title="Qdrant Management",
    description="API for Qdrant Management",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(collection.router, prefix="/api/collections", tags=["collections"])
app.include_router(document.router, prefix="/api/documents", tags=["documents"])
