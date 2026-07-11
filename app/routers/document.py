from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database import get_session
import app.dependencies.services as dependencies_services
import app.dependencies.auth as dependencies_auth
from app.services import DocumentService
from app.schemas.document import DocumentRead, DocumentCreate
from app.schemas.user import User

router = APIRouter(tags=["documents"])

@router.get(
"/{collection_id}/documents",
    response_model=list[DocumentRead],
    summary="Get all documents in a collection")
async def get_documents(
    collection_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_service: DocumentService = Depends(dependencies_services.get_document_service)
):
    return await document_service.get_documents(session=session, user=user, collection_id=collection_id)

@router.get(
"/{collection_id}/documents/{document_id}",
    response_model=DocumentRead,
    summary="Get document by id")
async def get_document(
    collection_id: int,
    document_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_service: DocumentService = Depends(dependencies_services.get_document_service)
):
    return await document_service.get_document(
        session=session,
        user=user,
        collection_id=collection_id,
        document_id=document_id
    )

@router.post(
"/{collection_id}/documents/",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload new document")
async def upload_document(
    collection_id: int,
    payload: DocumentCreate,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_service: DocumentService = Depends(dependencies_services.get_document_service)
):
    return await document_service.add_document(
        session=session,
        user=user,
        collection_id=collection_id,
        document=payload
    )

@router.delete(
"/{collection_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete document")
async def delete_document(
    collection_id: int,
    document_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_service: DocumentService = Depends(dependencies_services.get_document_service)
):
    return await document_service.delete_document(
        session=session,
        user=user,
        collection_id=collection_id,
        document_id=document_id
    )