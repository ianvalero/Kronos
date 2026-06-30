from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import asyncio
from celery.signals import worker_process_init
from llama_index.embeddings.openai import OpenAIEmbedding

from app.config.settings import settings
from app.models.document import DocumentVersionDB
from app.celery_workers.celery_app import celery_app

if TYPE_CHECKING:
    from app.services.qdrant_service import QdrantService
    from app.services.redis_service import RedisService

logger = logging.getLogger(f"app.{__name__}")
qdrant_service: QdrantService | None = None
redis_service: RedisService | None = None

@worker_process_init.connect
def init_worker_connections(**kwargs):
    global qdrant_service, redis_service

    from app.services.qdrant_service import QdrantService
    from app.services.redis_service import RedisService

    logger.info("Starting worker process. Initializing connections...")
    qdrant_service = QdrantService()
    redis_service = RedisService()

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="tasks.process_document_version"
)
def process_document_version(self, document_version: DocumentVersionDB):
    try:
        self.update_state(state="PROGRESS", meta={"step": "reading", "document_id": document_version.document_id})
        logger.info(f"Processing document version: {document_version.id} - {document_version.filename}")

        if not asyncio.run(qdrant_service.get_collection(document_version.document.collection)):
            self.update_state(state="FAILURE", meta={"error": "Collection not found"})
            logger.error(f"Collection {document_version.document.collection} not found")
            return False

    except Exception as err:
        self.update_state(state="FAILURE", meta={"error": str(err)})
        logger.exception(f"Error processing document version: {document_version.id} - {document_version.filename}")

def _embedding_file(saved_file_path: str):
    vector_store = qdrant_service.get_vector_store()

    _embedding = OpenAIEmbedding(
        model_name=settings.embedding_model_name,
        api_base=settings.embedding_base_url,
        api_key="EMPTY",
        embed_batch_size=32,
    )

