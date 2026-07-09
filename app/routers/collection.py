from fastapi import APIRouter, status, Depends
from sqlmodel import Session

from app.database import get_session
from app.services.collection_service import CollectionService
import app.dependencies.services as dependencies_services
import app.dependencies.auth as dependencies_auth
import app.schemas.collection as CollectionSchema
from app.schemas.user import User

router = APIRouter(tags=["collections"])

@router.get(
"/",
    response_model=CollectionSchema.CollectionsResponse,
    summary="Get all collection")
async def get_collections(
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.get_collections(session=session, user=user)


@router.get(
"/{collection_id}",
    response_model=CollectionSchema.CollectionRead,
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
    response_model=CollectionSchema.CollectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection")
async def create_collection(
    body: CollectionSchema.CollectionCreate,
    session: Session = Depends(get_session),
    user: User = Depends(dependencies_auth.get_current_user),
    collection_service: CollectionService = Depends(dependencies_services.get_collection_service)
):
    return await collection_service.create_collection(session=session, user=user, new_collection=body)


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