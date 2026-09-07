from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.documents import get_rag_service


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
