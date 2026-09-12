import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.conversations.service import ConversationService
from app.routers import chat, cowork, documents
from app.schemas.config import Settings, settings
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.utils.logger import get_logger
from app.workspace.manager import WorkspaceService

logger = get_logger(__name__)


def build_lifespan(config: Settings):
    @asynccontextmanager
    async def configured_lifespan(_app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting %s v%s", config.APP_NAME, config.APP_VERSION)
        logger.info("Model: %s", config.MODEL_NAME)
        logger.info("Threads: %s", config.N_THREADS)
        try:
            yield
        finally:
            if llm_service.is_loaded:
                await asyncio.to_thread(llm_service.unload_model)
            await asyncio.to_thread(rag_service.close)
            await asyncio.to_thread(_app.state.conversation_service.close)
            logger.info("Shutting down")

    return configured_lifespan


def create_app(config: Settings = settings) -> FastAPI:
    """Build an application with environment-specific production safeguards."""
    application = FastAPI(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        description="Qwen LLM local chat and document retrieval API",
        docs_url=None if config.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if config.ENVIRONMENT == "production" else "/redoc",
        openapi_url=None if config.ENVIRONMENT == "production" else "/openapi.json",
        lifespan=build_lifespan(config),
    )
    application.state.settings = config
    application.state.conversation_service = ConversationService(config.COWORK_DB_PATH)
    application.state.workspace_service = WorkspaceService(
        config.COWORK_WORKSPACE_ROOT,
        max_file_bytes=config.COWORK_MAX_FILE_BYTES,
    )

    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.allowed_hosts_list,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    @application.middleware("http")
    async def add_security_headers(request: Request, call_next):
        if request.url.path == "/api/v1/documents/upload":
            content_length = request.headers.get("content-length")
            try:
                declared_length = int(content_length) if content_length else None
            except ValueError:
                declared_length = None
            if (
                declared_length is not None
                and declared_length > config.MAX_UPLOAD_BYTES + 2_000_000
            ):
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body exceeds the upload limit"},
                )
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    application.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    application.include_router(documents.router, prefix="/api/v1", tags=["documents"])
    application.include_router(cowork.router, prefix="/api/v1", tags=["cowork"])

    @application.get("/")
    async def root() -> dict[str, str]:
        result = {
            "name": config.APP_NAME,
            "version": config.APP_VERSION,
        }
        if config.ENVIRONMENT != "production":
            result["docs"] = "/docs"
        return result

    return application


app = create_app()
