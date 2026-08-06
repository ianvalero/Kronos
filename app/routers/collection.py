from typing import Annotated
from fastapi import APIRouter, status, Depends, Query
from sqlmodel import Session

from app.database import get_session
from app.services.collection_service import CollectionService
import app.dependencies.services as dependencies_services
import app.dependencies.auth as dependencies_auth
import app.schemas.collection as CollectionSchema
from app.schemas.pagination import Pagination, PaginatedResponse
from app.schemas.user import User

router = APIRouter(prefix="/api/collections", tags=["Collections"])

@router.get(
"/",
    response_model=PaginatedResponse[CollectionSchema.CollectionReadDetails],
    summary="Get all collection")
async def get_collections(
    params: Annotated[CollectionSchema.CollectionQueryParams, Query()],
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    items, total = await collection_service.get_collections(
        session=session,
        user=user,
        filters=params,
        offset=params.offset,
        limit=params.limit
    )
    pagination = Pagination(
        offset=params.offset,
        limit=params.limit,
        total=total,
        has_next=params.offset + params.limit < total,
        has_prev=params.offset > 0
    )

    return PaginatedResponse[CollectionSchema.CollectionReadDetails](
        items=items,
        pagination=pagination
    )


@router.get(
"/{collection_id}",
    response_model=CollectionSchema.CollectionReadDetails,
    summary="Get collection")
async def get_collection(
    collection_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.get_collection(session=session, user=user, collection_id=collection_id)


@router.post(
"/",
    response_model=CollectionSchema.CollectionReadDetails,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection")
async def create_collection(
    body: CollectionSchema.CollectionCreate,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.create_collection(session=session, user=user, new_collection=body)

@router.patch(
    "/{collection_id}",
    response_model=CollectionSchema.CollectionReadDetails,
    status_code=status.HTTP_200_OK,
    summary="Update collection")
async def update_collection(
    collection_id: int,
    body: CollectionSchema.CollectionUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.update_collection(session=session, user=user, collection_id=collection_id, data=body)

@router.delete(
"/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection")
async def delete_collection(
    collection_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.delete_collection(session=session, user=user, collection_id=collection_id)