from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.chat import get_llm_service, get_model_router
from app.schemas.config import Settings, settings
from app.services.llm_service import llm_service


class FakeLLMService:
    def __init__(self, loaded: bool = True) -> None:
        self.is_loaded = loaded
        self.model_info_calls = 0
        self.unload_calls = 0

    def get_model_info(self) -> dict[str, Any]:
        self.model_info_calls += 1
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
        self.unload_calls += 1
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
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    # Tests must not inherit an operator token or host allowlist from a
    # developer's untracked .env file.
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "MODEL_MODE", "local")
    monkeypatch.setattr(settings, "REMOTE_MODELS_ENABLED", False)
    allowed_host = next(
        middleware.kwargs["allowed_hosts"][0]
        for middleware in app.user_middleware
        if middleware.cls.__name__ == "TrustedHostMiddleware"
    )
    with TestClient(app, base_url=f"http://{allowed_host}") as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["remote_models_enabled"] is False
    assert data["active_provider"] is None
    assert data["selected_model"] is None
    assert data["fallback_available"] is False


def test_model_info_is_available_when_unloaded(client: TestClient) -> None:
    fake = FakeLLMService(loaded=False)
    app.dependency_overrides[get_llm_service] = lambda: fake
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    assert response.json()["loaded"] is False


@pytest.mark.parametrize("path", ["/api/v1/model/info", "/api/v1/models"])
def test_model_surfaces_require_access_when_token_is_configured(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
) -> None:
    app.dependency_overrides[get_llm_service] = lambda: FakeLLMService(loaded=False)
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "configured-access-token")

    response = client.get(path)

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("path", "method"),
    [
        ("/api/v1/model/info", "get"),
        ("/api/v1/model/unload", "post"),
    ],
)
def test_protected_lifecycle_routes_accept_the_configured_bearer_token(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    method: str,
) -> None:
    fake = FakeLLMService()
    app.dependency_overrides[get_llm_service] = lambda: fake
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "test-token")

    unauthenticated = getattr(client, method)(path)
    # FastAPI resolves non-auth dependencies before rejecting this request, so
    # count only the authenticated route invocation below.
    fake.model_info_calls = 0
    fake.unload_calls = 0
    authenticated = getattr(client, method)(path, headers={"Authorization": "Bearer test-token"})

    assert unauthenticated.status_code == 401
    assert authenticated.status_code == 200
    if method == "get":
        assert fake.model_info_calls >= 1
    else:
        assert fake.unload_calls == 1


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


def test_models_catalog_has_typed_public_shape(client: TestClient) -> None:
    class FakeRouter:
        def list_models(self, refresh: bool = False) -> dict[str, Any]:
            assert refresh is False
            return {
                "object": "list",
                "data": [
                    {
                        "id": "kilo-auto/free",
                        "name": "Kilo Auto Free",
                        "provider": "kilo",
                        "free": True,
                        "supports_chat": True,
                        "context_length": None,
                    }
                ],
                "providers": [{"name": "kilo", "configured": True, "available": True}],
            }

    app.dependency_overrides[get_model_router] = FakeRouter
    response = client.get("/api/v1/models")

    assert response.status_code == 200
    assert response.json()["data"][0]["provider"] == "kilo"


def test_streaming_completion_terminates_with_done(client: TestClient) -> None:
    app.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
    response = client.post(
        "/api/v1/chat/completions/stream",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert response.status_code == 200
    assert "data: [DONE]" in response.text


def test_openai_stream_flag_uses_the_standard_completions_endpoint(client: TestClient) -> None:
    app.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
    response = client.post(
        "/api/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello"}], "stream": True},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data: [DONE]" in response.text


def test_streaming_completion_requires_an_available_route(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeLLMService(loaded=False)
    app.dependency_overrides[get_llm_service] = lambda: fake
    monkeypatch.setattr(settings, "MODEL_MODE", "local")
    monkeypatch.setattr(settings, "REMOTE_MODELS_ENABLED", False)

    response = client.post(
        "/api/v1/chat/completions/stream",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": []},
        {"messages": [{"role": "invalid", "content": "Hello"}]},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user", "content": "Hello"}], "temperature": None},
        {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 0},
        {
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": settings.MAX_CONTEXT_LENGTH + 1,
        },
    ],
)
def test_chat_request_validation(client: TestClient, payload: dict[str, Any]) -> None:
    response = client.post("/api/v1/chat/completions", json=payload)
    assert response.status_code == 422


def test_llm_service_singleton() -> None:
    assert llm_service is llm_service.get_instance()


def test_default_settings_are_valid() -> None:
    config = Settings(_env_file=None)
    assert config.HOST == "127.0.0.1"
    assert config.N_THREADS > 0
    assert config.MAX_CONTEXT_LENGTH > 0
    assert config.MAX_TOKENS <= config.MAX_CONTEXT_LENGTH
    assert config.MODEL_FILE.endswith(".gguf")
    assert config.RAG_CHUNK_OVERLAP < config.RAG_CHUNK_SIZE
    assert config.allowed_origins_list


def test_default_free_order_is_provider_safe() -> None:
    config = Settings(_env_file=None)
    assert config.MODEL_MODE == "auto_free"
    assert config.free_provider_order == ("kilo", "opencode", "openrouter", "local")
    assert config.REMOTE_MODELS_ENABLED is False


def test_remote_mode_requires_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("QWENDBC_ACCESS_TOKEN", raising=False)
    with pytest.raises(ValueError, match="QWENDBC_ACCESS_TOKEN"):
        Settings(_env_file=None, REMOTE_MODELS_ENABLED=True)


@pytest.mark.parametrize(
    "provider_order",
    ["kilo,kilo,local", "kilo,unknown,local"],
)
def test_settings_reject_invalid_free_provider_order(provider_order: str) -> None:
    with pytest.raises(ValueError, match="FREE_PROVIDER_ORDER"):
        Settings(_env_file=None, FREE_PROVIDER_ORDER=provider_order)


def test_settings_reject_max_tokens_above_context() -> None:
    with pytest.raises(ValueError, match="MAX_TOKENS"):
        Settings(_env_file=None, MAX_CONTEXT_LENGTH=1024, MAX_TOKENS=2048)
