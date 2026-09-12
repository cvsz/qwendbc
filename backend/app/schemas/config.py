from functools import lru_cache
import re
from typing import ClassVar, Literal
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import __version__


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Qwen LLM App"
    APP_VERSION: ClassVar[str] = __version__
    ENVIRONMENT: Literal["development", "production"] = "development"
    DEBUG: bool = False

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = Field(default=8000, ge=1, le=65535)
    TRUST_PROXY_HEADERS: bool = False

    # Model
    MODEL_NAME: str = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    MODEL_FILE: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    MODEL_REVISION: str = Field(default="", max_length=64, repr=False)
    MODEL_SHA256: str = Field(default="", max_length=64, repr=False)
    MODEL_PATH: str = "./models"
    MAX_CONTEXT_LENGTH: int = Field(default=4096, ge=512, le=131072)
    N_THREADS: int = Field(default=4, ge=1, le=256)
    N_BATCH: int = Field(default=512, ge=1, le=8192)

    # Free-model routing. Remote access is deliberately opt-in.
    MODEL_MODE: Literal["local", "auto_free"] = "auto_free"
    FREE_PROVIDER_ORDER: str = "kilo,opencode,openrouter,local"
    REMOTE_MODELS_ENABLED: bool = False
    QWENDBC_ACCESS_TOKEN: str = Field(default="", repr=False)
    REMOTE_REQUEST_TIMEOUT_SECONDS: int = Field(default=60, ge=1, le=300)
    REMOTE_MAX_CONCURRENT_REQUESTS: int = Field(default=4, ge=1, le=32)
    REMOTE_RATE_LIMIT_PER_MINUTE: int = Field(default=30, ge=1, le=1000)

    # Hosted provider endpoints and optional credentials.
    KILO_BASE_URL: str = Field(default="https://api.kilo.ai/api/gateway", pattern=r"^https?://")
    KILO_API_KEY: str = Field(default="", repr=False)
    KILO_MODEL: str = Field(default="kilo-auto/free", min_length=1)
    OPENCODE_BASE_URL: str = Field(default="https://opencode.ai/zen/v1", pattern=r"^https?://")
    OPENCODE_API_KEY: str = Field(default="", repr=False)
    OPENCODE_FREE_MODEL: str = Field(default="auto", min_length=1)
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1", pattern=r"^https?://")
    OPENROUTER_API_KEY: str = Field(default="", repr=False)
    OPENROUTER_MODEL: str = Field(default="openrouter/free", min_length=1)

    # Generation
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    TOP_P: float = Field(default=0.9, ge=0.0, le=1.0)
    MAX_TOKENS: int = Field(default=2048, ge=1, le=32768)

    # RAG / document retrieval
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_REVISION: str = Field(default="", max_length=64, repr=False)
    RAG_COLLECTION: str = "documents"
    RAG_CHUNK_SIZE: int = Field(default=1000, ge=100, le=10000)
    RAG_CHUNK_OVERLAP: int = Field(default=150, ge=0, le=5000)
    RAG_EMBED_BATCH_SIZE: int = Field(default=32, ge=1, le=256)
    MAX_RAG_CHUNKS: int = Field(default=100_000, ge=1, le=1_000_000)
    MAX_UPLOAD_BYTES: int = Field(default=5_000_000, ge=1024, le=5_000_000)

    # Cowork / AionUi-inspired local workspace runtime
    COWORK_DB_PATH: str = "./data/cowork.sqlite3"
    COWORK_WORKSPACE_ROOT: str = "./workspaces"
    COWORK_MAX_FILE_BYTES: int = Field(default=1_000_000, ge=1_024, le=10_000_000)

    # Agentic task/control-plane persistence. Kept separate from Cowork storage
    # so task schema evolution cannot silently reinterpret conversation data.
    AGENTIC_DB_PATH: str = "./data/agentic.sqlite3"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,testserver"

    # Request bounds
    MAX_CHAT_CONTENT_BYTES: int = Field(default=1_000_000, ge=1_024, le=10_000_000)

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return [origin for origin in origins if origin]

    @property
    def allowed_hosts_list(self) -> list[str]:
        hosts = [host.strip().lower() for host in self.ALLOWED_HOSTS.split(",")]
        return [host for host in hosts if host]

    @property
    def free_provider_order(self) -> tuple[str, ...]:
        return tuple(provider.strip().lower() for provider in self.FREE_PROVIDER_ORDER.split(","))

    @model_validator(mode="after")
    def validate_cross_field_settings(self) -> "Settings":
        allowed_providers = {"kilo", "opencode", "openrouter", "local"}
        provider_order = self.free_provider_order
        if not provider_order or any(
            provider not in allowed_providers for provider in provider_order
        ):
            raise ValueError("FREE_PROVIDER_ORDER contains an unknown provider")
        if len(provider_order) != len(set(provider_order)):
            raise ValueError("FREE_PROVIDER_ORDER must not contain duplicate providers")
        if provider_order[-1] != "local":
            raise ValueError("FREE_PROVIDER_ORDER must keep local as the final fallback")
        token = self.QWENDBC_ACCESS_TOKEN.strip()
        if self.REMOTE_MODELS_ENABLED:
            if not token:
                raise ValueError(
                    "QWENDBC_ACCESS_TOKEN is required when REMOTE_MODELS_ENABLED is true"
                )
        if self.ENVIRONMENT == "production":
            if not token:
                raise ValueError("QWENDBC_ACCESS_TOKEN is required in production")
            if len(token) < 32:
                raise ValueError(
                    "QWENDBC_ACCESS_TOKEN must be at least 32 characters in production"
                )
        if token != self.QWENDBC_ACCESS_TOKEN or any(char.isspace() for char in token):
            raise ValueError("QWENDBC_ACCESS_TOKEN must not contain whitespace")
        if self.ENVIRONMENT == "production" and self.DEBUG:
            raise ValueError("DEBUG must be false in production")
        checksum = self.MODEL_SHA256.strip()
        if checksum and not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
            raise ValueError("MODEL_SHA256 must be a 64-character hexadecimal digest")
        if self.ENVIRONMENT == "production" and not checksum:
            raise ValueError("MODEL_SHA256 is required in production")
        for field_name in ("MODEL_REVISION", "EMBEDDING_MODEL_REVISION"):
            revision = getattr(self, field_name).strip()
            if revision and any(char.isspace() for char in revision):
                raise ValueError(f"{field_name} must not contain whitespace")
            if self.ENVIRONMENT == "production" and not re.fullmatch(r"[0-9a-f]{40}", revision):
                raise ValueError(
                    f"{field_name} must be a 40-character immutable commit in production"
                )
        for field_name in ("KILO_BASE_URL", "OPENCODE_BASE_URL", "OPENROUTER_BASE_URL"):
            endpoint = urlparse(getattr(self, field_name))
            if not endpoint.netloc or endpoint.scheme not in {"http", "https"}:
                raise ValueError(f"{field_name} must be a valid HTTP(S) URL")
            if self.ENVIRONMENT == "production" and endpoint.scheme != "https":
                raise ValueError(f"{field_name} must use HTTPS in production")
        if "/" in self.MODEL_FILE or "\\" in self.MODEL_FILE:
            raise ValueError("MODEL_FILE must be a filename without path separators")
        if not self.MODEL_FILE.lower().endswith(".gguf"):
            raise ValueError("MODEL_FILE must point to a .gguf file")
        if self.MAX_TOKENS > self.MAX_CONTEXT_LENGTH:
            raise ValueError("MAX_TOKENS must not exceed MAX_CONTEXT_LENGTH")
        if self.RAG_CHUNK_OVERLAP >= self.RAG_CHUNK_SIZE:
            raise ValueError("RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE")
        if not self.allowed_origins_list:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin")
        if self.ENVIRONMENT == "production" and "*" in self.allowed_origins_list:
            raise ValueError("ALLOWED_ORIGINS must be explicit in production")
        if not self.allowed_hosts_list or "*" in self.allowed_hosts_list:
            raise ValueError("ALLOWED_HOSTS must contain explicit hosts")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
