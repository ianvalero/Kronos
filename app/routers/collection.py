from fastapi import APIRouter, HTTPException, status, Depends

import app.dependencies as dependencies
import app.schemas.collection as CollectionSchema
from app.services.qdrant_service import QdrantService

router = APIRouter()

@router.get(
"/",
    tags=["collections"],
    response_model=CollectionSchema.CollectionsResponse,
    summary="Get all collection")
async def get_collections(qdrant_service: QdrantService = Depends(dependencies.get_qdrant_service)):
    return await qdrant_service.get_collections()


@router.get(
"/{collection_name}",
    tags=["collections"],
    response_model=CollectionSchema.Collection,
    summary="Get collection")
async def get_collection(
        collection_name: str,
        qdrant_service: QdrantService = Depends(dependencies.get_qdrant_service)
):
    try:
        return await qdrant_service.get_collection(collection_name)
    except Exception as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post(
"/",
    tags=["collections"],
    response_model=CollectionSchema.Collection,
    status_code=status.HTTP_201_CREATED,
    summary="Create collection")
async def create_collection(
        body: CollectionSchema.CollectionCreate,
        qdrant_service: QdrantService = Depends(dependencies.get_qdrant_service)
):
    try:
        return await qdrant_service.create_collection(body)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.delete(
"/{collection_name}",
    tags=["collections"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete collection")
async def delete_collection(
        collection_name: str,
        qdrant_service: QdrantService = Depends(dependencies.get_qdrant_service)
):
    try:
        await qdrant_service.delete_collection(collection_name)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))