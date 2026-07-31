from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session

from app.database import get_session
import app.dependencies.services as dependencies_services
import app.dependencies.auth as dependencies_auth
from app.services import DocumentService
from app.schemas.document import DocumentRead, DocumentCreate, DocumentUpdate
from app.schemas.pagination import Pagination, PaginatedResponse
from app.schemas.user import User


router = APIRouter(tags=["documents"])

@router.get(
"/{collection_id}/documents",
    response_model=PaginatedResponse[DocumentRead],
    summary="Get all documents in a collection")
async def get_documents(
    collection_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_service: DocumentService = Depends(dependencies_services.get_document_service)
):
    items, total = await document_service.get_documents(
        session=session,
        user=user,
        collection_id=collection_id,
        offset=offset,
        limit=limit
    )
    pagination = Pagination(
        offset=offset,
        limit=limit,
        total=total,
        has_next=offset + limit < total,
        has_prev=offset > 0
    )

    return PaginatedResponse[DocumentRead](
        items=items,
        pagination=pagination
    )


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
    summary="Create new document")
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

@router.patch(
"/{collection_id}/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Update document")
async def update_document(
    collection_id: int,
    document_id: int,
    payload: DocumentUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    document_service: DocumentService = Depends(dependencies_services.get_document_service)
):
    return await document_service.update_document(
        session=session,
        user=user,
        collection_id=collection_id,
        document_id=document_id,
        data=payload
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