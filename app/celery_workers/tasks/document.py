import logging
import asyncio
import os

from celery.exceptions import MaxRetriesExceededError
from celery.signals import worker_process_init
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import SimpleDirectoryReader
from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.core.schema import MetadataMode
from sqlmodel import Session

from app.config.settings import settings
from app.services.qdrant_service import QdrantService
from app.services.sql_service import SqlService
from app.celery_workers.celery_app import celery_app
from app.database import engine

logger = logging.getLogger(f"app.{__name__}")

qdrant_service: QdrantService | None = None
sql_service: SqlService | None = None
embedding_model: OpenAIEmbedding | None = None

@worker_process_init.connect
def init_worker_connections(**kwargs):
    """Se ejecuta una vez por proceso worker, no por tarea, para reutilizar conexiones."""
    global qdrant_service, sql_service, embedding_model

    logger.info("Starting worker process. Initializing connections...")
    qdrant_service = QdrantService()
    sql_service = SqlService()
    embedding_model = OpenAIEmbedding(
        model_name=settings.embedding_model_name,
        api_base=settings.embedding_base_url,
        api_key="EMPTY",
        embed_batch_size=32,
    )


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="tasks.process_document_version"
)
def process_document_version(self, document_version_id: int):
    with Session(engine) as session:
        document_version = sql_service.get_document_version(document_version_id, session)
        if not document_version:
            logger.error(f"Document version {document_version_id} not found in database")
            return False

        collection_name = document_version.document.collection

        try:
            sql_service.update_document_version_status(
                document_version_id=document_version_id,
                status="processing",
                session=session
            )

            self.update_state(
                state="PROGRESS",
                meta={"step": "reading", "document_id": document_version.document_id}
            )
            logger.info(f"Processing document version: {document_version.id} - {document_version.filename}")

            if not asyncio.run(qdrant_service.collection_exists(collection_name)):
                raise ValueError(f"Collection {collection_name} not found")

            point_ids = asyncio.run(_embed_and_upload(
                file_path=document_version.file_path,
                collection_name=collection_name,
                document_version_id=document_version.id,
            ))

            sql_service.update_document_version_status(
                document_version_id=document_version_id,
                status="completed",
                session=session,
                qdrant_point_ids=point_ids
            )

            logger.info(f"Document version {document_version.id} processed: {len(point_ids)} points")
            _delete_local_file(file_path=document_version.file_path)

            return {"document_version_id": document_version.id, "points_count": len(point_ids)}

        except Exception as err:
            logger.exception(f"Error processing document version: {document_version.id}")

            sql_service.update_document_version_status(
                document_version_id=document_version_id,
                status="failed",
                session=session,
                error_message=str(err),
                increment_attempts=True
            )

            self.update_state(state="FAILURE", meta={"error": str(err)})

            try:
                raise self.retry(exc=err)
            except MaxRetriesExceededError:
                _delete_local_file(document_version.id)
                raise


async def _embed_and_upload(file_path: str, collection_name: str, document_version_id: int) -> list[int]:
    # 1. Leer el fichero y partirlo en nodos (chunks)
    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    nodes = splitter.get_nodes_from_documents(documents)

    if not nodes:
        return []

    for node in nodes:
        node.metadata["document_version_id"] = document_version_id

    # 2. Generar embeddings para cada nodo (en batch, usando el modelo del servidor Spark)
    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes]
    embeddings = await embedding_model.aget_text_embedding_batch(texts)

    for node, embedding in zip(nodes, embeddings):
        node.embedding = embedding

    # 3. Subir los nodos (con sus embeddings) a Qdrant
    vector_store = await qdrant_service.get_vector_store(collection_name)
    point_ids = await vector_store.async_add(nodes)

    return [int(pid) for pid in point_ids]


def _delete_local_file(file_path: str):
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Local file deleted: {file_path}")
    except Exception as e:
        # No queremos que un fallo al borrar el fichero tumbe la task
        logger.error(f"Error deleting local file {file_path}")
        logger.exception(e)