from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.config import settings


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=200_000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=128)
    temperature: float = Field(default=settings.TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=settings.TOP_P, ge=0.0, le=1.0)
    max_tokens: int = Field(default=settings.MAX_TOKENS, ge=1, le=32768)


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int]


class DocumentQuery(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    top_k: int = Field(default=5, ge=1, le=50)


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_added: int


class DocumentSearchResult(BaseModel):
    id: str
    document: str
    metadata: dict[str, Any]
    distance: float | None = None


class DocumentSearchResponse(BaseModel):
    results: list[DocumentSearchResult]


class HealthResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    version: str
    model_loaded: bool
    timestamp: datetime


class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    path: str | None
    context_length: int
    threads: int
    loaded: bool
