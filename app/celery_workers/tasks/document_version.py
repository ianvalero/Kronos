import asyncio
import logging
import os

from celery.exceptions import MaxRetriesExceededError
from celery.signals import worker_process_init, worker_process_shutdown
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.embeddings.openai import OpenAIEmbedding
from sqlmodel import Session

from app.celery_workers.celery_app import celery_app
from app.config.settings import settings
from app.database import engine
from app.infrastructure.qdrant_gateway import QdrantGateway
from app.repositories.document_version import DocumentVersionRepository

logger = logging.getLogger(f"app.{__name__}")

qdrant_service: QdrantGateway | None = None
document_version_repository: DocumentVersionRepository | None = None
embedding_model: OpenAIEmbedding | None = None
worker_loop: asyncio.AbstractEventLoop | None = None


@worker_process_init.connect
def init_worker_connections(**kwargs):
    global qdrant_service, document_version_repository, embedding_model, worker_loop

    logger.info("Starting worker process. Initializing connections...")

    worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(worker_loop)

    qdrant_service = QdrantGateway()
    document_version_repository = DocumentVersionRepository()
    embedding_model = OpenAIEmbedding(
        model_name=settings.embedding_model_name,
        api_base=settings.embedding_base_url,
        api_key="EMPTY",
        embed_batch_size=32,
    )


@worker_process_shutdown.connect
def shutdown_worker_connections(**kwargs):
    global worker_loop

    if worker_loop is not None and not worker_loop.is_closed():
        logger.info("Shutting down worker process. Closing event loop...")
        worker_loop.close()


def run_async(coro):
    return worker_loop.run_until_complete(coro)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="tasks.process_document_version",
)
def process_document_version(self, document_version_id: int):
    with Session(engine) as session:
        document_version = document_version_repository.get_document_version(session, document_version_id)
        if not document_version:
            logger.error(f"Document version {document_version_id} not found in database")
            return False

        collection_name = document_version.document.collection.qdrant_name

        try:
            document_version_repository.update_document_version_status(
                document_version_id=document_version_id,
                status="processing",
                session=session,
            )

            self.update_state(
                state="PROGRESS",
                meta={"step": "reading", "document_id": document_version.document_id},
            )
            logger.info(f"Processing document version: {document_version.id} - {document_version.filename}")

            if not run_async(qdrant_service.collection_exists(collection_name)):
                raise ValueError(f"Collection {collection_name} not found")

            point_ids = run_async(
                _embed_and_upload(
                    file_path=document_version.file_path,
                    collection_name=collection_name,
                    document_version_id=document_version.id,
                )
            )

            document_version_repository.update_document_version_status(
                document_version_id=document_version_id,
                status="completed",
                session=session,
                qdrant_point_ids=point_ids,
            )
            logger.info(f"Document version {document_version.id} processed: {len(point_ids)} points")

            _archive_previous_versions(
                document_id=document_version.document_id,
                current_version_id=document_version.id,
                collection_name=collection_name,
                session=session,
            )

            _delete_local_file(file_path=document_version.file_path)
            return {"document_version_id": document_version.id, "points_count": len(point_ids)}

        except Exception as err:
            logger.exception(f"Error processing document version: {document_version.id}")

            document_version_repository.update_document_version_status(
                document_version_id=document_version_id,
                status="failed",
                session=session,
                error_message=str(err),
                increment_attempts=True,
            )

            try:
                raise self.retry(exc=err)
            except MaxRetriesExceededError:
                _delete_local_file(document_version.file_path)
                raise


async def _embed_and_upload(file_path: str, collection_name: str, document_version_id: int) -> list[str]:
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()

    splitter = SentenceSplitter(
        chunk_size=settings.embedding_chunk_size,
        chunk_overlap=settings.embedding_chunk_overlap,
    )
    nodes = splitter.get_nodes_from_documents(documents)

    if not nodes:
        return []

    for node in nodes:
        node.metadata["document_version_id"] = document_version_id

    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes]
    embeddings = await embedding_model.aget_text_embedding_batch(texts)

    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding

    vector_store = await qdrant_service.get_vector_store(collection_name)
    point_ids = await vector_store.async_add(nodes)

    return [str(pid) for pid in point_ids]


def _delete_local_file(file_path: str) -> bool:
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Local file deleted: {file_path}")
        return True

    except Exception:
        logger.exception(f"Error deleting local file {file_path}")
        return False


def _archive_previous_versions(document_id: int, current_version_id: int, collection_name: str, session: Session) -> None:
    completed_versions = document_version_repository.get_document_completed_versions(session, document_id)

    previous_versions = [
        version for version in completed_versions
        if version.id != current_version_id
    ]

    for version in previous_versions:
        if version.qdrant_point_ids:
            try:
                run_async(
                    qdrant_service.delete_points(
                        collection_name=collection_name,
                        point_ids=version.qdrant_point_ids,
                    )
                )
            except Exception:
                logger.exception(f"Failed to delete Qdrant points for version {version.id}")
                continue

        document_version_repository.update_document_version_status(
            document_version_id=version.id,
            status="archived",
            session=session,
        )

    if previous_versions:
        logger.info(f"Archived {len(previous_versions)} previous version(s) of document {document_id}")