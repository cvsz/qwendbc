from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Qwen LLM App"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Model
    MODEL_NAME: str = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    MODEL_FILE: str = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    MODEL_PATH: str = "./models"
    MAX_CONTEXT_LENGTH: int = 4096
    N_THREADS: int = 4
    N_BATCH: int = 512

    # Generation
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    MAX_TOKENS: int = 2048

    # RAG
    CHROMA_DB_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
