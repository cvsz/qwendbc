from fastapi import APIRouter, HTTPException, Depends
from typing import List
import asyncio

from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessage,
    HealthResponse, ModelInfo, DocumentUpload, DocumentQuery
)
from app.schemas.config import settings
from app.services.llm_service import llm_service
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_llm_service():
    """Dependency to get LLM service instance"""
    return llm_service


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health status"""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "model_loaded": llm_service.is_loaded,
        "timestamp": datetime.now(timezone.utc)
    }


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(service=Depends(get_llm_service)):
    """Get information about the loaded model"""
    if not service.is_loaded:
        raise HTTPException(status_code=400, detail="Model not loaded")
    return service.get_model_info()


@router.post("/model/load")
async def load_model(service=Depends(get_llm_service)):
    """Load the LLM model"""
    if service.is_loaded:
        return {"status": "already_loaded"}
    
    success = await asyncio.to_thread(service.load_model)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load model")
    
    return {"status": "loaded", "model": settings.MODEL_NAME}


@router.post("/model/unload")
async def unload_model(service=Depends(get_llm_service)):
    """Unload the LLM model"""
    if not service.is_loaded:
        return {"status": "not_loaded"}
    
    service.unload_model()
    return {"status": "unloaded"}


@router.post("/chat/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    service=Depends(get_llm_service)
):
    """Generate chat completions"""
    if not service.is_loaded:
        raise HTTPException(status_code=400, detail="Model not loaded")
    
    try:
        messages = [msg.dict() for msg in request.messages]
        response = await asyncio.to_thread(
            service.generate,
            messages=messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat completion failed: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during chat completion")


@router.post("/chat/completions/stream")
async def chat_completions_stream(
    request: ChatRequest,
    service=Depends(get_llm_service)
):
    """Stream chat completions"""
    from fastapi.responses import StreamingResponse
    import json
    
    if not service.is_loaded:
        raise HTTPException(status_code=400, detail="Model not loaded")
    
    async def generate():
        try:
            messages = [msg.dict() for msg in request.messages]
            for chunk in service.generate_stream(
                messages=messages,
                temperature=request.temperature,
                top_p=request.top_p,
                max_tokens=request.max_tokens
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Stream failed: {type(e).__name__} - {e}", exc_info=True)
            # Return generic error message to avoid exposing internal details
            yield f"data: {json.dumps({'error': 'An error occurred while processing your request'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
