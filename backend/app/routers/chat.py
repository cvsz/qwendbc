import asyncio
import json
from collections.abc import Generator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.routers.documents import get_rag_service
from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse, ModelInfo, ModelsResponse
from app.schemas.config import settings
from app.services.llm_service import LLMService, llm_service
from app.services.model_router import ModelRouter
from app.services.provider_types import ProviderError
from app.services.rag_service import RAGService
from app.services.access_control import require_access
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_llm_service() -> LLMService:
    return llm_service


def get_model_router(service: LLMService = Depends(get_llm_service)) -> ModelRouter:
    return ModelRouter(service)


async def _inject_rag_context(
    messages: list[dict[str, object]], request: ChatRequest, rag: RAGService
) -> tuple[list[dict[str, object]], list[dict[str, object]] | None]:
    if not request.use_rag:
        return messages, None
    last_user_index = next(
        (index for index in range(len(messages) - 1, -1, -1) if messages[index]["role"] == "user"),
        None,
    )
    if last_user_index is None:
        return messages, None
    try:
        rag_sources = await asyncio.to_thread(
            rag.search, str(messages[last_user_index]["content"]), request.rag_top_k
        )
    except Exception as exc:
        logger.exception("Document retrieval failed")
        raise HTTPException(status_code=503, detail="Document index is unavailable") from exc
    if not rag_sources:
        return messages, rag_sources

    context_lines = ["Retrieved context:"]
    remaining = 12_000
    for index, source in enumerate(rag_sources, start=1):
        filename = source.get("metadata", {}).get("filename", "document")
        document = str(source.get("document", ""))[:2_000]
        line = f"[{index}] {filename}\n{document}"
        if len(line) > remaining:
            break
        context_lines.append(line)
        remaining -= len(line)
    if len(context_lines) > 1:
        messages.insert(last_user_index, {"role": "system", "content": "\n".join(context_lines)})
    return messages, rag_sources


@router.get("/health", response_model=HealthResponse)
async def health_check() -> dict[str, object]:
    model_router = ModelRouter(llm_service)
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "model_loaded": llm_service.is_loaded,
        "timestamp": datetime.now(timezone.utc),
        "providers": [item.model_dump() for item in model_router.provider_statuses()],
        **model_router.routing_state(),
    }


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(
    model_router: ModelRouter = Depends(get_model_router),
) -> dict[str, object]:
    return model_router.get_model_info()


@router.post("/model/load")
async def load_model(
    service: LLMService = Depends(get_llm_service), _: None = Depends(require_access)
) -> dict[str, str]:
    if service.is_loaded:
        return {"status": "already_loaded", "model": settings.MODEL_NAME}

    success = await asyncio.to_thread(service.load_model)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")
    return {"status": "loaded", "model": settings.MODEL_NAME}


@router.post("/model/unload")
async def unload_model(
    service: LLMService = Depends(get_llm_service), _: None = Depends(require_access)
) -> dict[str, str]:
    if not service.is_loaded:
        return {"status": "not_loaded"}
    await asyncio.to_thread(service.unload_model)
    return {"status": "unloaded"}


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    model_router: ModelRouter = Depends(get_model_router),
    rag: RAGService = Depends(get_rag_service),
    _: None = Depends(require_access),
) -> dict[str, object]:
    messages = [message.model_dump() for message in request.messages]
    messages, rag_sources = await _inject_rag_context(messages, request, rag)
    try:
        return await asyncio.to_thread(
            model_router.complete,
            messages=messages,
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            rag_sources=rag_sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=exc.public_message) from exc
    except Exception as exc:
        logger.exception("Chat completion failed")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during chat completion",
        ) from exc


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: ChatRequest,
    model_router: ModelRouter = Depends(get_model_router),
    rag: RAGService = Depends(get_rag_service),
    _: None = Depends(require_access),
) -> StreamingResponse:
    validate_request = getattr(model_router, "validate_request", None)
    if callable(validate_request):
        try:
            validate_request(provider=request.provider, model=request.model)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    elif not model_router.local_service.is_loaded and not getattr(
        model_router, "_remote_enabled", False
    ):
        raise HTTPException(status_code=400, detail="Model not loaded")

    messages, _rag_sources = await _inject_rag_context(
        [message.model_dump() for message in request.messages], request, rag
    )

    # Keep this a synchronous generator. Starlette iterates sync response bodies in a
    # worker thread, preventing CPU-bound llama.cpp iteration from blocking the event loop.
    def event_stream() -> Generator[str, None, None]:
        try:
            for chunk in model_router.stream(
                messages=messages,
                provider=request.provider,
                model=request.model,
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


@router.get("/models", response_model=ModelsResponse)
async def list_models(model_router: ModelRouter = Depends(get_model_router)) -> ModelsResponse:
    return model_router.list_models()


@router.post("/models/refresh", response_model=ModelsResponse)
async def refresh_models(
    model_router: ModelRouter = Depends(get_model_router), _: None = Depends(require_access)
) -> ModelsResponse:
    return model_router.list_models(refresh=True)
