from fastapi import APIRouter, status, Depends, HTTPException
from sqlmodel import Session

from app.database import get_session
from app.services.qdrant_service import QdrantService
from app.services.collection_service import CollectionService
import app.dependencies.services as dependencies_services
import app.dependencies.auth as dependencies_auth
import app.schemas.collection as CollectionSchema

router = APIRouter()

@router.get(
"/",
    tags=["collections"],
    response_model=CollectionSchema.CollectionsResponse,
    summary="Get all collection")
async def get_collections(
    session: Session = Depends(get_session),
    current_user: "UserDB" = Depends(dependencies_auth.get_current_user),
    qdrant_service: QdrantService = Depends(dependencies_services.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.get_collections(session, qdrant_service, current_user)


@router.get(
"/{collection_id}",
    tags=["collections"],
    response_model=CollectionSchema.CollectionRead,
    summary="Get collection")
async def get_collection(
    collection_id: int,
    current_user: "UserDB" = Depends(dependencies_auth.get_current_user),
    session: Session = Depends(get_session),
    qdrant_service: QdrantService = Depends(dependencies_services.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.get_collection(session, qdrant_service, collection_id)


@router.post(
"/",
    tags=["collections"],
    response_model=CollectionSchema.CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection")
async def create_collection(
    body: CollectionSchema.CollectionCreate,
    current_user: "UserDB" = Depends(dependencies_auth.get_current_user),
    session: Session = Depends(get_session),
    qdrant_service: QdrantService = Depends(dependencies_services.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    user_groups = {group.id for group in current_user.groups}
    if body.group_id not in user_groups:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to create a collection in this group."
        )

    return await collection_service.create_collection(session, qdrant_service, body)


@router.delete(
"/{collection_id}",
    tags=["collections"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection")
async def delete_collection(
    collection_id: int,
    current_user: "UserDB" = Depends(dependencies_auth.get_current_user),
    session: Session = Depends(get_session),
    qdrant_service: QdrantService = Depends(dependencies_services.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.delete_collection(session, qdrant_service, collection_id)