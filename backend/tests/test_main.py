from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.chat import get_llm_service
from app.schemas.config import Settings
from app.services.llm_service import llm_service


class FakeLLMService:
    def __init__(self, loaded: bool = True) -> None:
        self.is_loaded = loaded

    def get_model_info(self) -> dict[str, Any]:
        return {
            "name": "test-model",
            "path": "/tmp/test.gguf" if self.is_loaded else None,
            "context_length": 4096,
            "threads": 4,
            "loaded": self.is_loaded,
        }

    def load_model(self) -> bool:
        self.is_loaded = True
        return True

    def unload_model(self) -> None:
        self.is_loaded = False

    def generate(self, **_: Any) -> dict[str, Any]:
        return {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1,
            "model": "test-model",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    def generate_stream(self, **_: Any) -> Generator[dict[str, Any], None, None]:
        yield {
            "id": "chatcmpl-test",
            "object": "chat.completion.chunk",
            "created": 1,
            "model": "test-model",
            "choices": [{"index": 0, "delta": {"content": "hi"}, "finish_reason": None}],
        }


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_model_info_is_available_when_unloaded(client: TestClient) -> None:
    fake = FakeLLMService(loaded=False)
    app.dependency_overrides[get_llm_service] = lambda: fake
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    assert response.json()["loaded"] is False


def test_chat_completion_requires_loaded_model(client: TestClient) -> None:
    fake = FakeLLMService(loaded=False)
    app.dependency_overrides[get_llm_service] = lambda: fake
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 400


def test_chat_completion_success(client: TestClient) -> None:
    app.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "hello"


def test_streaming_completion_terminates_with_done(client: TestClient) -> None:
    app.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
    response = client.post(
        "/api/v1/chat/completions/stream",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    assert "data: [DONE]" in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": []},
        {"messages": [{"role": "invalid", "content": "Hello"}]},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user", "content": "Hello"}], "temperature": None},
        {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 0},
    ],
)
def test_chat_request_validation(client: TestClient, payload: dict[str, Any]) -> None:
    response = client.post("/api/v1/chat/completions", json=payload)
    assert response.status_code == 422


def test_llm_service_singleton() -> None:
    assert llm_service is llm_service.get_instance()


def test_default_settings_are_valid() -> None:
    config = Settings(_env_file=None)
    assert config.N_THREADS > 0
    assert config.MAX_CONTEXT_LENGTH > 0
    assert config.MODEL_FILE.endswith(".gguf")
    assert config.RAG_CHUNK_OVERLAP < config.RAG_CHUNK_SIZE
    assert config.allowed_origins_list
