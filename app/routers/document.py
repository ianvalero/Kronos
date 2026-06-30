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
        redis_service = Depends(dependencies.get_redis_service)
):
    payload = DocumentSchema.DocumentVersionCreate(
        saved_file_path=await util.save_document_version_file(file=file),
        filename=file.filename,
        uploaded_by=uploaded_by,
        file_size=file.size,
        mime_type=file.content_type
    )
    document_version = sql_service.add_document_version(document_id, payload, session)
    redis_service.add_document_version(document_version)
    #TODO LLamar al worker de Celeri
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
        redis_service = Depends(dependencies.get_redis_service)
):
    if sql_service.delete_document(document_id, payload, session) is None:
        raise HTTPException(status_code=404, detail="Document not found")

    #redis_service.delete_document(document_id)