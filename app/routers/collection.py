from fastapi import APIRouter, status, Depends
from sqlmodel import Session

from app.database import get_session
from app.infrastructure.qdrant_gateway import QdrantGateway
from app.services.collection_service import CollectionService
import app.dependencies.services as dependencies_services
import app.dependencies.infrastructure as dependencies_infrastructure
import app.dependencies.auth as dependencies_auth
import app.schemas.collection as CollectionSchema
from app.schemas.user import User

router = APIRouter()

@router.get(
"/",
    tags=["collections"],
    response_model=CollectionSchema.CollectionsResponse,
    summary="Get all collection")
async def get_collections(
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    qdrant_service: QdrantGateway = Depends(dependencies_infrastructure.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.get_collections(
        session=session,
        qdrant=qdrant_service,
        user=user
    )


@router.get(
"/{collection_id}",
    tags=["collections"],
    response_model=CollectionSchema.CollectionRead,
    summary="Get collection")
async def get_collection(
    collection_id: int,
    user: User = Depends(dependencies_auth.get_current_user),
    session: Session = Depends(get_session),
    qdrant_service: QdrantGateway = Depends(dependencies_infrastructure.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.get_collection(
        session=session,
        qdrant=qdrant_service,
        user=user,
        collection_id=collection_id
    )


@router.post(
"/",
    tags=["collections"],
    response_model=CollectionSchema.CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection")
async def create_collection(
    body: CollectionSchema.CollectionCreate,
    user: User = Depends(dependencies_auth.get_current_user),
    session: Session = Depends(get_session),
    qdrant_service: QdrantGateway = Depends(dependencies_infrastructure.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.create_collection(
        session=session,
        qdrant=qdrant_service,
        user=user,
        new_collection=body
    )


@router.delete(
"/{collection_id}",
    tags=["collections"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection")
async def delete_collection(
    collection_id: int,
    user: User = Depends(dependencies_auth.get_current_user),
    session: Session = Depends(get_session),
    qdrant_service: QdrantGateway = Depends(dependencies_infrastructure.get_qdrant_service),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.delete_collection(
        session=session,
        qdrant=qdrant_service,
        user=user,
        collection_id=collection_id
    )