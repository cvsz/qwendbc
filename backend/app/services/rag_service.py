import json
import math
import sqlite3
import threading
import uuid
from array import array
from pathlib import Path
from typing import Any, Iterable

from app.schemas.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


_MAX_EMBEDDING_DIMENSION = 16_384


class RAGService:
    """Lazy local document embedding and retrieval service backed by SQLite."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._connection: sqlite3.Connection | None = None
        self._embedding_model: Any = None

    def _ensure_ready(self) -> None:
        if self._connection is not None and self._embedding_model is not None:
            return

        with self._lock:
            if self._connection is not None and self._embedding_model is not None:
                return

            from sentence_transformers import SentenceTransformer

            storage_dir = Path(settings.CHROMA_DB_PATH)
            storage_dir.mkdir(parents=True, exist_ok=True)
            try:
                storage_dir.chmod(0o700)
            except OSError:
                logger.warning("Could not restrict RAG storage directory permissions")

            connection = sqlite3.connect(
                storage_dir / "rag.sqlite3",
                check_same_thread=False,
                timeout=30.0,
            )
            try:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute("PRAGMA journal_mode = WAL")
                connection.execute("PRAGMA synchronous = FULL")
                connection.execute("PRAGMA trusted_schema = OFF")
                connection.execute("PRAGMA busy_timeout = 30000")
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                        id TEXT PRIMARY KEY,
                        document TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        embedding BLOB NOT NULL
                    )
                    """)
                connection.commit()
                try:
                    (storage_dir / "rag.sqlite3").chmod(0o600)
                except OSError:
                    logger.warning("Could not restrict RAG database file permissions")

                if settings.EMBEDDING_MODEL_REVISION:
                    embedding_model = SentenceTransformer(
                        settings.EMBEDDING_MODEL,
                        revision=settings.EMBEDDING_MODEL_REVISION,
                    )
                else:
                    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            except Exception:
                connection.close()
                raise

            self._connection = connection
            self._embedding_model = embedding_model
            logger.info("Initialized local RAG store")

    @staticmethod
    def _normalize_text(content: str) -> str:
        lines = content.replace("\r\n", "\n").split("\n")
        return "\n".join(line.rstrip() for line in lines).strip()

    def _chunk_text(self, content: str) -> list[str]:
        text = self._normalize_text(content)
        if not text:
            raise ValueError("Document is empty")

        size = settings.RAG_CHUNK_SIZE
        overlap = settings.RAG_CHUNK_OVERLAP
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = end - overlap
        return chunks

    @staticmethod
    def _embedding_values(embedding: Any) -> list[float]:
        values = embedding.tolist() if hasattr(embedding, "tolist") else embedding
        if not isinstance(values, Iterable):
            raise ValueError("Embedding output must be a numeric sequence")
        result = [float(value) for value in values]
        if not result or len(result) > _MAX_EMBEDDING_DIMENSION:
            raise ValueError("Embedding dimension is outside the supported bounds")
        if any(not math.isfinite(value) for value in result):
            raise ValueError("Embedding output contains a non-finite value")
        return result

    @classmethod
    def _serialize_embedding(cls, embedding: Any) -> bytes:
        return array("f", cls._embedding_values(embedding)).tobytes()

    @staticmethod
    def _deserialize_embedding(raw: bytes) -> list[float]:
        values = array("f")
        values.frombytes(raw)
        return [float(value) for value in values]

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or not left:
            return 0.0
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        similarity = sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)
        return max(-1.0, min(1.0, similarity))

    def add_document(
        self,
        filename: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        with self._lock:
            self._ensure_ready()
            assert self._connection is not None
            chunks = self._chunk_text(content)
            embeddings = self._embedding_model.encode(
                chunks,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            source_metadata = json.dumps(metadata or {}, ensure_ascii=False, default=str)
            rows = []
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                chunk_metadata = {
                    "filename": filename,
                    "chunk_index": index,
                    "source_metadata": source_metadata,
                }
                rows.append(
                    (
                        f"doc-{uuid.uuid4().hex}",
                        chunk,
                        json.dumps(chunk_metadata, ensure_ascii=False),
                        sqlite3.Binary(self._serialize_embedding(embedding)),
                    )
                )
            with self._connection:
                self._connection.executemany(
                    """
                    INSERT INTO rag_chunks (id, document, metadata_json, embedding)
                    VALUES (?, ?, ?, ?)
                    """,
                    rows,
                )
            return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            self._ensure_ready()
            assert self._connection is not None
            if top_k < 1:
                raise ValueError("top_k must be at least 1")

            query_embedding = self._embedding_model.encode(
                [query],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            query_values = self._embedding_values(query_embedding[0])
            rows = self._connection.execute(
                "SELECT id, document, metadata_json, embedding FROM rag_chunks"
            ).fetchall()
            if not rows:
                return []

            results: list[dict[str, Any]] = []
            for item_id, document, metadata_json, raw_embedding in rows:
                try:
                    metadata = json.loads(metadata_json)
                except (TypeError, json.JSONDecodeError):
                    metadata = {}
                similarity = self._cosine_similarity(
                    query_values,
                    self._deserialize_embedding(raw_embedding),
                )
                results.append(
                    {
                        "id": item_id,
                        "document": document,
                        "metadata": metadata if isinstance(metadata, dict) else {},
                        "distance": 1.0 - similarity,
                    }
                )
            results.sort(key=lambda result: float(result["distance"]))
            return results[:top_k]

    def close(self) -> None:
        with self._lock:
            if self._connection is not None:
                self._connection.close()
            self._connection = None
            self._embedding_model = None


rag_service = RAGService()
