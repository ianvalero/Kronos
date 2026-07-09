from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlmodel import Session

from app.database import get_session
import app.utils.document as util
import app.dependencies.services as dependencies_services
import app.dependencies.auth as dependencies_auth
from app.services import DocumentVersionService
from app.schemas.document import DocumentRead
from app.schemas.document_version import DocumentVersion, DocumentVersionPayload, DocumentVersionTaskRead
from app.schemas.user import User

router = APIRouter(tags=["documents versions"])

@router.get(
"/{document_id}/versions",
    response_model=list[DocumentRead],
    summary="Get all document versions")
async def get_document_versions(
    document_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_version_service: DocumentVersionService = Depends(dependencies_services.get_document_version_service)
):
    return document_version_service.get_document_versions(
        session=session,
        user=user,
        document_id=document_id
    )

@router.get(
"/{document_id}/versions/{document_version_id}",
    response_model=list[DocumentRead],
    summary="Get a document versions")
async def get_document_version(
    document_id: int,
    document_version_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_version_service: DocumentVersionService = Depends(dependencies_services.get_document_version_service)
):
    return document_version_service.get_document_version(
        session=session,
        user=user,
        document_id=document_id,
        document_version_id=document_version_id
    )






# TODO ---------------------------------------------------------
@router.post(
"/{document_id}",
    response_model=DocumentVersion,
    summary="Upload new document version")
async def upload_document_version(
    document_id: int,
    payload: DocumentVersionPayload,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_version_service: DocumentVersionService = Depends(dependencies_services.get_document_service),
    #celery_service = Depends(dependencies.get_celery_service)
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

@router.get(
"/tasks/{task_id}",
    response_model=DocumentSchema.DocumentVersionTaskRead,
    summary="Get document by id")
async def get_task(
    task_id: str,
    celery_service = Depends(dependencies.get_celery_service)
):
    task = celery_service.get_task_status(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task