import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.chat import DocumentQuery, DocumentSearchResponse, DocumentUploadResponse
from app.schemas.config import settings
from app.services.rag_service import RAGService, rag_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_rag_service() -> RAGService:
    return rag_service


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    service: RAGService = Depends(get_rag_service),
) -> DocumentUploadResponse:
    filename = file.filename or "document.txt"
    raw = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_BYTES} byte limit",
        )

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only UTF-8 text documents are supported",
        ) from exc

    if not content.strip():
        raise HTTPException(status_code=422, detail="Document is empty")

    try:
        chunks_added = await asyncio.to_thread(
            service.add_document,
            filename,
            content,
            {"content_type": file.content_type or "application/octet-stream"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Document ingestion failed")
        raise HTTPException(status_code=503, detail="Document index is unavailable") from exc

    return DocumentUploadResponse(filename=filename, chunks_added=chunks_added)


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentQuery,
    service: RAGService = Depends(get_rag_service),
) -> DocumentSearchResponse:
    try:
        results = await asyncio.to_thread(service.search, request.query, request.top_k)
    except Exception as exc:
        logger.exception("Document search failed")
        raise HTTPException(status_code=503, detail="Document index is unavailable") from exc
    return DocumentSearchResponse(results=results)
