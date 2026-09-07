import json
import threading
import uuid
from typing import Any

from app.schemas.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """Lazy local document embedding and retrieval service backed by ChromaDB."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._client: Any = None
        self._collection: Any = None
        self._embedding_model: Any = None

    def _ensure_ready(self) -> None:
        if self._collection is not None and self._embedding_model is not None:
            return

        with self._lock:
            if self._collection is not None and self._embedding_model is not None:
                return

            import chromadb
            from sentence_transformers import SentenceTransformer

            logger.info("Initializing RAG store at %s", settings.CHROMA_DB_PATH)
            self._client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            self._collection = self._client.get_or_create_collection(
                name=settings.RAG_COLLECTION
            )
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

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

    def add_document(
        self,
        filename: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        with self._lock:
            self._ensure_ready()
            chunks = self._chunk_text(content)
            embeddings = self._embedding_model.encode(
                chunks,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).tolist()
            source_metadata = json.dumps(metadata or {}, ensure_ascii=False, default=str)
            ids = [f"doc-{uuid.uuid4().hex}" for _ in chunks]
            metadatas = [
                {
                    "filename": filename,
                    "chunk_index": index,
                    "source_metadata": source_metadata,
                }
                for index in range(len(chunks))
            ]
            self._collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        with self._lock:
            self._ensure_ready()
            count = int(self._collection.count())
            if count == 0:
                return []

            query_embedding = self._embedding_model.encode(
                [query],
                normalize_embeddings=True,
                show_progress_bar=False,
            ).tolist()
            response = self._collection.query(
                query_embeddings=query_embedding,
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
            ids = (response.get("ids") or [[]])[0]
            documents = (response.get("documents") or [[]])[0]
            metadatas = (response.get("metadatas") or [[]])[0]
            distances = (response.get("distances") or [[]])[0]

            results: list[dict[str, Any]] = []
            for index, item_id in enumerate(ids):
                results.append(
                    {
                        "id": item_id,
                        "document": documents[index] or "",
                        "metadata": metadatas[index] or {},
                        "distance": (
                            float(distances[index])
                            if distances[index] is not None
                            else None
                        ),
                    }
                )
            return results


rag_service = RAGService()
