from functools import lru_cache

from pydantic import Field, model_validator

from app import __version__
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    APP_VERSION: str = __version__
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)

    # Model
    MODEL_NAME: str = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    MODEL_FILE: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    MODEL_PATH: str = "./models"
    MAX_CONTEXT_LENGTH: int = Field(default=4096, ge=512, le=131072)
    N_THREADS: int = Field(default=4, ge=1, le=256)
    N_BATCH: int = Field(default=512, ge=1, le=8192)

    # Generation
    TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    TOP_P: float = Field(default=0.9, ge=0.0, le=1.0)
    MAX_TOKENS: int = Field(default=2048, ge=1, le=32768)

    # RAG / document retrieval
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RAG_COLLECTION: str = "documents"
    RAG_CHUNK_SIZE: int = Field(default=1000, ge=100, le=10000)
    RAG_CHUNK_OVERLAP: int = Field(default=150, ge=0, le=5000)
    MAX_UPLOAD_BYTES: int = Field(default=5_000_000, ge=1024, le=100_000_000)

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return [origin for origin in origins if origin]

    @model_validator(mode="after")
    def validate_cross_field_settings(self) -> "Settings":
        if not self.MODEL_FILE.lower().endswith(".gguf"):
            raise ValueError("MODEL_FILE must point to a .gguf file")
        if self.RAG_CHUNK_OVERLAP >= self.RAG_CHUNK_SIZE:
            raise ValueError("RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE")
        if not self.allowed_origins_list:
            raise ValueError("ALLOWED_ORIGINS must contain at least one origin")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
