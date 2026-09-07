import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, documents
from app.schemas.config import settings
from app.services.llm_service import llm_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Model: %s", settings.MODEL_NAME)
    logger.info("Threads: %s", settings.N_THREADS)
    try:
        yield
    finally:
        if llm_service.is_loaded:
            await asyncio.to_thread(llm_service.unload_model)
        logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Qwen LLM local chat and document retrieval API",
    lifespan=lifespan,
)

origins = settings.allowed_origins_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
