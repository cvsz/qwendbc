from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.chat import get_model_router
from app.schemas.chat import ChatRequest
from app.schemas.config import Settings


class RouterService:
    is_loaded = False

    def get_model_info(self) -> dict[str, Any]:
        return {
            "name": "test-model",
            "path": None,
            "context_length": 4096,
            "threads": 4,
            "loaded": False,
        }


def test_model_router_dependency_is_reused_for_the_same_service() -> None:
    service = RouterService()

    first = get_model_router(service)  # type: ignore[arg-type]
    second = get_model_router(service)  # type: ignore[arg-type]

    assert first is second


def test_production_app_disables_docs_and_rejects_untrusted_hosts() -> None:
    config = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        ALLOWED_HOSTS="example.test",
        QWENDBC_ACCESS_TOKEN="production-test-token-with-at-least-32-characters",
        MODEL_REVISION="a" * 40,
        EMBEDDING_MODEL_REVISION="b" * 40,
        MODEL_SHA256="c" * 64,
    )
    production_app = create_app(config)

    with TestClient(production_app, base_url="http://example.test") as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/", headers={"host": "attacker.example"}).status_code == 400


def test_production_app_applies_its_access_token_to_protected_routes() -> None:
    config = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        ALLOWED_HOSTS="example.test",
        QWENDBC_ACCESS_TOKEN="production-test-token-with-at-least-32-characters",
        MODEL_REVISION="a" * 40,
        EMBEDDING_MODEL_REVISION="b" * 40,
        MODEL_SHA256="c" * 64,
    )
    production_app = create_app(config)

    with TestClient(production_app, base_url="http://example.test") as client:
        assert client.get("/api/v1/model/info").status_code == 401


def test_remote_mode_requires_a_strong_production_access_token() -> None:
    with pytest.raises(ValueError, match="QWENDBC_ACCESS_TOKEN"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            REMOTE_MODELS_ENABLED=True,
            QWENDBC_ACCESS_TOKEN="short-token",
        )


def test_production_requires_access_control_even_for_local_mode() -> None:
    with pytest.raises(ValueError, match="QWENDBC_ACCESS_TOKEN"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            MODEL_MODE="local",
            REMOTE_MODELS_ENABLED=False,
        )


def test_production_requires_immutable_model_revisions() -> None:
    with pytest.raises(ValueError, match="MODEL_REVISION"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            MODEL_MODE="local",
            REMOTE_MODELS_ENABLED=False,
            QWENDBC_ACCESS_TOKEN="production-test-token-with-at-least-32-characters",
            MODEL_SHA256="c" * 64,
        )


def test_production_requires_a_model_checksum() -> None:
    with pytest.raises(ValueError, match="MODEL_SHA256"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            MODEL_MODE="local",
            REMOTE_MODELS_ENABLED=False,
            QWENDBC_ACCESS_TOKEN="production-test-token-with-at-least-32-characters",
            MODEL_REVISION="a" * 40,
            EMBEDDING_MODEL_REVISION="b" * 40,
        )


def test_production_rejects_insecure_remote_provider_urls() -> None:
    with pytest.raises(ValueError, match="KILO_BASE_URL"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            QWENDBC_ACCESS_TOKEN="production-test-token-with-at-least-32-characters",
            MODEL_REVISION="a" * 40,
            EMBEDDING_MODEL_REVISION="b" * 40,
            MODEL_SHA256="c" * 64,
            KILO_BASE_URL="http://provider.example.test/api",
        )


def test_chat_request_rejects_an_oversized_aggregate_payload() -> None:
    messages = [{"role": "user", "content": "x" * 200_000} for _ in range(6)]

    with pytest.raises(ValueError, match="total message content"):
        ChatRequest(messages=messages)


def test_model_file_cannot_escape_the_configured_model_directory() -> None:
    with pytest.raises(ValueError, match="MODEL_FILE"):
        Settings(_env_file=None, MODEL_FILE="../outside.gguf")
