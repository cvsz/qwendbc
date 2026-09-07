import asyncio
import json
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse, ModelInfo
from app.schemas.config import settings
from app.services.llm_service import LLMService, llm_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_llm_service() -> LLMService:
    return llm_service


@router.get("/health", response_model=HealthResponse)
async def health_check() -> dict[str, object]:
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "model_loaded": llm_service.is_loaded,
        "timestamp": datetime.now(timezone.utc),
    }


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(service: LLMService = Depends(get_llm_service)) -> dict[str, object]:
    return service.get_model_info()


@router.post("/model/load")
async def load_model(service: LLMService = Depends(get_llm_service)) -> dict[str, str]:
    if service.is_loaded:
        return {"status": "already_loaded", "model": settings.MODEL_NAME}

    success = await asyncio.to_thread(service.load_model)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")
    return {"status": "loaded", "model": settings.MODEL_NAME}


@router.post("/model/unload")
async def unload_model(service: LLMService = Depends(get_llm_service)) -> dict[str, str]:
    if not service.is_loaded:
        return {"status": "not_loaded"}
    await asyncio.to_thread(service.unload_model)
    return {"status": "unloaded"}


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    service: LLMService = Depends(get_llm_service),
) -> dict[str, object]:
    if not service.is_loaded:
        raise HTTPException(status_code=400, detail="Model not loaded")

    messages = [message.model_dump() for message in request.messages]
    try:
        return await asyncio.to_thread(
            service.generate,
            messages=messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
        )
    except Exception as exc:
        logger.exception("Chat completion failed")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during chat completion",
        ) from exc


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: ChatRequest,
    service: LLMService = Depends(get_llm_service),
) -> StreamingResponse:
    if not service.is_loaded:
        raise HTTPException(status_code=400, detail="Model not loaded")

    messages = [message.model_dump() for message in request.messages]

    # Keep this a synchronous generator. Starlette iterates sync response bodies in a
    # worker thread, preventing CPU-bound llama.cpp iteration from blocking the event loop.
    def event_stream() -> Generator[str, None, None]:
        try:
            for chunk in service.generate_stream(
                messages=messages,
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception:
            logger.exception("Streaming chat completion failed")
            yield f"data: {json.dumps({'error': 'Internal server error'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
