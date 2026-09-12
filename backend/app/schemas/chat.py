from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.config import settings


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=200_000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=128)
    # OpenAI-compatible clients such as Open WebUI send this flag to the same
    # completions endpoint instead of using AI-DBC's legacy /stream path.
    stream: bool = False
    temperature: float = Field(default=settings.TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=settings.TOP_P, ge=0.0, le=1.0)
    max_tokens: int = Field(
        default=settings.MAX_TOKENS,
        ge=1,
        le=settings.MAX_CONTEXT_LENGTH,
    )
    provider: str | None = Field(default=None, min_length=1, max_length=64)
    model: str | None = Field(default=None, min_length=1, max_length=256)
    use_rag: bool = False
    rag_top_k: int = Field(default=5, ge=1, le=50)

    @model_validator(mode="after")
    def validate_total_message_content(self) -> "ChatRequest":
        total_bytes = sum(len(message.content.encode("utf-8")) for message in self.messages)
        if total_bytes > settings.MAX_CHAT_CONTENT_BYTES:
            raise ValueError("total message content exceeds MAX_CHAT_CONTENT_BYTES")
        return self


class ProviderStatus(BaseModel):
    name: str
    configured: bool
    available: bool


class ModelCatalogItem(BaseModel):
    id: str
    name: str
    provider: str
    free: bool
    supports_chat: bool
    context_length: int | None = None


class ModelsResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelCatalogItem]
    providers: list[ProviderStatus]
    cached_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRoutingMetadata(BaseModel):
    provider: str
    model: str
    fallback: bool
    rag_sources: list[dict[str, Any]] | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, Any] = Field(default_factory=dict)
    ai_dbc: ChatRoutingMetadata | None = Field(default=None, alias="ai-dbc")


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
    providers: list[ProviderStatus] = Field(default_factory=list)
    active_provider: str | None = None
    selected_model: str | None = None
    remote_models_enabled: bool = False
    fallback_available: bool = False


class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    path: str | None
    context_length: int
    threads: int
    loaded: bool
    providers: list[ProviderStatus] = Field(default_factory=list)
    active_provider: str | None = None
    selected_model: str | None = None
    remote_models_enabled: bool = False
    fallback_available: bool = False
