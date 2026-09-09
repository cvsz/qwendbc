from collections.abc import Generator
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.chat import get_model_router
from app.routers.documents import get_rag_service
from app.schemas.config import settings
from app.services.rag_service import RAGService


class FakeRAGService:
    def add_document(
        self,
        filename: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        assert filename
        assert content
        assert metadata is not None
        return 2

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        assert query
        assert top_k >= 1
        return [
            {
                "id": "doc-1",
                "document": "matching text",
                "metadata": {"filename": "test.txt", "chunk_index": 0},
                "distance": 0.1,
            }
        ]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_rag_service] = lambda: FakeRAGService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_upload_document_requires_file(client: TestClient) -> None:
    response = client.post("/api/v1/documents/upload")
    assert response.status_code == 422


def test_upload_document_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Test document content", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json() == {"filename": "test.txt", "chunks_added": 2}


def test_upload_document_normalizes_untrusted_filename(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("../unsafe\nname.txt", b"Test document content", "text/plain")},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "unsafe name.txt"


def test_upload_rejects_non_utf8(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("binary.bin", b"\xff\xfe\x00", "application/octet-stream")},
    )
    assert response.status_code == 415


def test_search_rejects_empty_query(client: TestClient) -> None:
    response = client.post("/api/v1/search", json={"query": ""})
    assert response.status_code == 422


def test_search_returns_typed_results(client: TestClient) -> None:
    response = client.post("/api/v1/search", json={"query": "test query", "top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["metadata"]["filename"] == "test.txt"


def test_document_upload_requires_bearer_token_when_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.schemas.config import settings

    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", b"Test document content", "text/plain")},
    )

    assert response.status_code == 401


def test_chat_rag_injects_labeled_context_before_completion(client: TestClient) -> None:
    captured: dict[str, Any] = {}

    class FakeRouter:
        def complete(self, messages: list[dict[str, Any]], **_: Any) -> dict[str, Any]:
            captured["messages"] = messages
            return {
                "id": "chatcmpl-rag",
                "object": "chat.completion",
                "created": 1,
                "model": "test-model",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "qwendbc": {"provider": "local", "model": "test-model", "fallback": False},
            }

    app.dependency_overrides[get_model_router] = FakeRouter
    response = client.post(
        "/api/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "What is in the document?"}],
            "use_rag": True,
            "rag_top_k": 2,
        },
    )

    assert response.status_code == 200
    assert captured["messages"][-2] == {
        "role": "system",
        "content": "Retrieved context:\n[1] test.txt\nmatching text",
    }


def test_streaming_chat_rag_injects_labeled_context_before_completion(client: TestClient) -> None:
    captured: dict[str, Any] = {}

    class FakeRouter:
        local_service = type("Local", (), {"is_loaded": True})()
        _remote_enabled = False

        def stream(
            self, messages: list[dict[str, Any]], **_: Any
        ) -> Generator[dict[str, Any], None, None]:
            captured["messages"] = messages
            yield {
                "id": "chatcmpl-rag",
                "object": "chat.completion.chunk",
                "created": 1,
                "model": "test-model",
                "choices": [{"index": 0, "delta": {"content": "ok"}, "finish_reason": None}],
            }

    app.dependency_overrides[get_model_router] = FakeRouter
    response = client.post(
        "/api/v1/chat/completions/stream",
        json={
            "messages": [{"role": "user", "content": "What is in the document?"}],
            "use_rag": True,
        },
    )

    assert response.status_code == 200
    assert captured["messages"][-2] == {
        "role": "system",
        "content": "Retrieved context:\n[1] test.txt\nmatching text",
    }


def test_rag_persists_normalized_embeddings_without_remote_vector_server(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSentenceTransformer:
        def __init__(self, _: str, **__: Any) -> None:
            pass

        def encode(self, texts: list[str], **_: Any) -> list[list[float]]:
            return [[1.0, 0.0] if "apple" in text.lower() else [0.0, 1.0] for text in texts]

    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = FakeSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", fake_module)
    monkeypatch.setattr(settings, "CHROMA_DB_PATH", str(tmp_path / "rag-data"))

    service = RAGService()
    try:
        assert service.add_document("fruit.txt", "apple notes") == 1

        results = service.search("apple", top_k=1)

        assert results[0]["document"] == "apple notes"
        assert results[0]["metadata"]["filename"] == "fruit.txt"
    finally:
        service.close()


def test_rag_rejects_a_legacy_chroma_store_without_silent_data_loss(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = object  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", fake_module)
    storage_path = tmp_path / "rag-data"
    storage_path.mkdir()
    (storage_path / "chroma.sqlite3").write_bytes(b"legacy")
    monkeypatch.setattr(settings, "CHROMA_DB_PATH", str(storage_path))

    service = RAGService()
    try:
        with pytest.raises(RuntimeError, match="Legacy Chroma"):
            service.search("query")
    finally:
        service.close()


def test_rag_embeddings_are_batched_and_chunk_quota_is_enforced(
    tmp_path: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batches: list[int] = []

    class FakeSentenceTransformer:
        def __init__(self, _: str, **__: Any) -> None:
            pass

        def encode(self, texts: list[str], **_: Any) -> list[list[float]]:
            batches.append(len(texts))
            return [[1.0, 0.0] for _ in texts]

    fake_module = ModuleType("sentence_transformers")
    fake_module.SentenceTransformer = FakeSentenceTransformer  # type: ignore[attr-defined]
    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", fake_module)
    monkeypatch.setattr(settings, "CHROMA_DB_PATH", str(tmp_path / "rag-data"))
    monkeypatch.setattr(settings, "RAG_CHUNK_SIZE", 5)
    monkeypatch.setattr(settings, "RAG_CHUNK_OVERLAP", 0)
    monkeypatch.setattr(settings, "RAG_EMBED_BATCH_SIZE", 2)
    monkeypatch.setattr(settings, "MAX_RAG_CHUNKS", 3)

    service = RAGService()
    try:
        assert service.add_document("batch.txt", "123456789012345") == 3
        assert batches == [2, 1]
        with pytest.raises(ValueError, match="quota"):
            service.add_document("too-many.txt", "another document")
    finally:
        service.close()
