from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlmodel import Session

from app.database import get_session
import app.utils.document as util
import app.dependencies as dependencies
import app.schemas.document as DocumentSchema

router = APIRouter()

@router.get(
"/",
    tags=["documents"],
    response_model=list[DocumentSchema.DocumentRead],
    summary="Get all documents")
async def get_documents(
    session: Session = Depends(get_session),
    sql_service = Depends(dependencies.get_sql_service)
):
    return sql_service.get_documents(session)

@router.get(
"/{document_id}",
    tags=["documents"],
    response_model=DocumentSchema.DocumentRead,
    summary="Get document by id")
async def get_document(
    document_id: int,
    session: Session = Depends(get_session),
    sql_service = Depends(dependencies.get_sql_service)
):
    document = sql_service.get_document(document_id, session)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document

@router.get(
"/tasks/{task_id}",
    tags=["documents"],
    response_model=DocumentSchema.DocumentVersionTaskRead,
    summary="Get document by id")
async def get_task(
    task_id: int,
    celery_service = Depends(dependencies.get_celery_service)
):
    task = celery_service.get_task_status(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

@router.post(
"/",
    tags=["documents"],
    response_model=DocumentSchema.DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document")
async def upload_document(
    payload: DocumentSchema.DocumentCreate,
    session: Session = Depends(get_session),
    sql_service = Depends(dependencies.get_sql_service)
):
    document = sql_service.add_document(payload, session)
    return document

@router.post(
"/{document_id}",
    tags=["documents"],
    response_model=DocumentSchema.DocumentVersionRead,
    summary="Upload document version")
async def upload_document_version(
    document_id: int,
    file: UploadFile = File(...),
    uploaded_by: str = Form(None),
    session: Session = Depends(get_session),
    sql_service = Depends(dependencies.get_sql_service),
    celery_service = Depends(dependencies.get_celery_service)
):
    payload = DocumentSchema.DocumentVersionCreate(
        saved_file_path=await util.save_document_version_file(file=file),
        filename=file.filename,
        uploaded_by=uploaded_by,
        file_size=file.size,
        mime_type=file.content_type
    )

    document_version = sql_service.add_document_version(
        document_id=document_id,
        document_version=payload,
        session=session
    )

    try:
        task_id = celery_service.update_document_version(document_version_id=document_version.id)
        document_version = sql_service.set_document_version_task_id(
            document_version_id=document_version.id,
            task_id=task_id,
            session=session
        )
    except Exception as err:
        document_version = sql_service.update_document_version_status(
            document_version_id=document_version.id,
            status="failed",
            session=session,
            error_message=f"No se pudo encolar la tarea de procesamiento: {err}",
        )

    return document_version

@router.delete(
"/{document_id}",
    tags=["documents"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document")
async def delete_document(
    document_id: int,
    payload: DocumentSchema.DocumentDelete,
    session: Session = Depends(get_session),
    sql_service = Depends(dependencies.get_sql_service),
    qdrant_service = Depends(dependencies.get_qdrant_service),
):
    document = sql_service.get_document(document_id, session)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    active_version = document.documents_versions[0] if document.documents_versions else None
    if active_version and active_version.qdrant_point_ids:
        await qdrant_service.delete_points(document.collection, active_version.qdrant_point_ids)

    sql_service.delete_document(document_id, payload, session)