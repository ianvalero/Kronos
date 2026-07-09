from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from sqlmodel import Session

from app.database import get_session
import app.dependencies.services as dependencies_services
import app.dependencies.infrastructure as dependencies_infrastructure
import app.dependencies.auth as dependencies_auth
import app.schemas.document_version as DocumentVersionSchema
from app.schemas.user import User
from app.services import DocumentVersionService
from app.exceptions import CeleryTaskNotFoundError

router = APIRouter(tags=["documents versions"])

@router.get(
"/{document_id}/versions",
    response_model=list[DocumentVersionSchema.DocumentVersion],
    summary="Get all document versions")
async def get_document_versions(
    document_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_version_service: DocumentVersionService = Depends(dependencies_services.get_document_version_service)
):
    return await document_version_service.get_document_versions(
        session=session,
        user=user,
        document_id=document_id
    )

@router.get(
"/{document_id}/versions/{document_version_id}",
    response_model=DocumentVersionSchema.DocumentVersionDetail,
    summary="Get a document versions")
async def get_document_version(
    document_id: int,
    document_version_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_version_service: DocumentVersionService = Depends(dependencies_services.get_document_version_service)
):
    return await document_version_service.get_document_version(
        session=session,
        user=user,
        document_id=document_id,
        document_version_id=document_version_id
    )

@router.post(
"/{document_id}/version",
    response_model=DocumentVersionSchema.DocumentVersion,
    summary="Upload new document version")
async def upload_document_version(
    document_id: int,
    payload: DocumentVersionSchema.DocumentVersionPayload,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_version_service: DocumentVersionService = Depends(dependencies_services.get_document_service),
):
    return await document_version_service.add_document_version(
        session=session,
        user=user,
        document_id=document_id,
        file=file,
        document_version=payload
    )

@router.get(
"/tasks/{task_id}",
    response_model=DocumentVersionSchema.DocumentVersionTaskRead,
    summary="Get document version task info")
async def get_task(
    task_id: str,
    celery_service = Depends(dependencies_infrastructure.get_celery_service)
):
    task = celery_service.get_task_status(task_id=task_id)
    if not task:
        raise CeleryTaskNotFoundError("Task not found")

    return task