from collections.abc import Iterator
from typing import Any

import pytest

from app.schemas.chat import ModelsResponse
from app.schemas.config import Settings
from app.services import model_router
from app.services.model_router import ModelRouter
from app.services.provider_types import ProviderError, ProviderModel


class FakeLocalService:
    def __init__(self, *, loaded: bool, text: str = "local answer") -> None:
        self.is_loaded = loaded
        self.text = text

    def generate(self, **_: Any) -> dict[str, Any]:
        return completion(self.text, "local-model")

    def generate_stream(self, **_: Any) -> Iterator[dict[str, Any]]:
        yield stream_chunk(self.text, "local-model")

    def get_model_info(self) -> dict[str, Any]:
        return {
            "name": "local-model",
            "path": "/tmp/local.gguf" if self.is_loaded else None,
            "context_length": 4096,
            "threads": 4,
            "loaded": self.is_loaded,
        }


class FakeProvider:
    def __init__(
        self,
        name: str,
        *,
        text: str | None = None,
        error: ProviderError | None = None,
    ) -> None:
        self.name = name
        self.text = text
        self.error = error
        self.default_model = f"{name}-free"
        self.free_model_ids = frozenset({self.default_model})

    def is_configured(self) -> bool:
        return True

    def list_models(self, refresh: bool = False) -> list[ProviderModel]:
        return [
            ProviderModel(
                provider=self.name,
                id=self.default_model,
                name=f"{self.name} free",
                free=True,
            )
        ]

    def complete(self, **_: Any) -> dict[str, Any]:
        if self.error:
            raise self.error
        assert self.text is not None
        return completion(self.text, self.default_model)

    def stream(self, **_: Any) -> Iterator[dict[str, Any]]:
        if self.error:
            raise self.error
        assert self.text is not None
        yield stream_chunk(self.text, self.default_model)


def completion(text: str, model: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def stream_chunk(text: str, model: str) -> dict[str, Any]:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion.chunk",
        "created": 1,
        "model": model,
        "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
    }


def make_settings(**overrides: Any) -> Settings:
    return Settings(
        _env_file=None,
        REMOTE_MODELS_ENABLED=True,
        QWENDBC_ACCESS_TOKEN="test-access-token",
        **overrides,
    )


def test_auto_mode_uses_configured_order_and_skips_rate_limited_provider() -> None:
    providers = [
        FakeProvider("kilo", error=ProviderError("busy", retryable=True)),
        FakeProvider("opencode", text="answer"),
    ]
    router = ModelRouter(FakeLocalService(loaded=False), make_settings(), providers=providers)

    result = router.complete([{"role": "user", "content": "hello"}], max_tokens=16)

    assert result["choices"][0]["message"]["content"] == "answer"
    assert result["qwendbc"] == {
        "provider": "opencode",
        "model": "opencode-free",
        "fallback": True,
    }


def test_local_provider_is_final_fallback_when_loaded() -> None:
    providers = [FakeProvider("kilo", error=ProviderError("down", retryable=True))]
    router = ModelRouter(
        FakeLocalService(loaded=True, text="local answer"), make_settings(), providers=providers
    )

    result = router.complete([{"role": "user", "content": "hello"}], max_tokens=16)

    assert result["choices"][0]["message"]["content"] == "local answer"
    assert result["qwendbc"] == {"provider": "local", "model": "local-model", "fallback": True}


def test_stream_falls_back_only_before_first_content_chunk() -> None:
    providers = [
        FakeProvider("kilo", error=ProviderError("busy", retryable=True)),
        FakeProvider("opencode", text="answer"),
    ]
    router = ModelRouter(FakeLocalService(loaded=False), make_settings(), providers=providers)

    chunks = list(router.stream([{"role": "user", "content": "hello"}], max_tokens=16))

    assert chunks == [stream_chunk("answer", "opencode-free")]


def test_catalog_reports_only_non_secret_provider_status() -> None:
    router = ModelRouter(
        FakeLocalService(loaded=False), make_settings(), providers=[FakeProvider("kilo", text="answer")]
    )

    catalog = router.list_models()

    assert isinstance(catalog, ModelsResponse)
    assert catalog.data[0].model_dump() == {
        "id": "kilo-free",
        "name": "kilo free",
        "provider": "kilo",
        "free": True,
        "supports_chat": True,
        "context_length": None,
    }
    assert catalog.providers[0].model_dump() == {
        "name": "kilo",
        "configured": True,
        "available": True,
    }
    assert "key" not in repr(catalog).lower()


def test_catalog_refreshes_provider_after_the_router_ttl(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = FakeProvider("kilo", text="answer")
    router = ModelRouter(FakeLocalService(loaded=False), make_settings(), providers=[provider])
    refreshes: list[bool] = []

    def list_models(refresh: bool = False) -> list[ProviderModel]:
        refreshes.append(refresh)
        return [ProviderModel(provider="kilo", id="kilo-free", name="Kilo", free=True)]

    provider.list_models = list_models  # type: ignore[method-assign]
    monotonic = iter([100.0, 131.0, 131.0])
    monkeypatch.setattr(model_router.time, "monotonic", lambda: next(monotonic))

    router.list_models()
    router.list_models()

    assert refreshes == [False, True]


def test_explicit_model_rejects_an_unknown_or_non_free_model() -> None:
    router = ModelRouter(
        FakeLocalService(loaded=False), make_settings(), providers=[FakeProvider("kilo", text="answer")]
    )

    with pytest.raises(ValueError, match="eligible free"):
        router.complete(
            [{"role": "user", "content": "hello"}],
            provider="kilo",
            model="paid-model",
            max_tokens=16,
        )


def test_explicit_provider_uses_its_default_when_no_model_is_requested() -> None:
    provider = FakeProvider("opencode", text="answer")
    provider.default_model = "auto"
    provider.free_model_ids = frozenset({"mimo-v2.5-free"})
    provider.list_models = lambda refresh=False: [
        ProviderModel(provider="opencode", id="mimo-v2.5-free", name="MiMo", free=True)
    ]
    router = ModelRouter(FakeLocalService(loaded=False), make_settings(), providers=[provider])

    result = router.complete(
        [{"role": "user", "content": "hello"}], provider="opencode", max_tokens=16
    )

    assert result["choices"][0]["message"]["content"] == "answer"
    assert result["qwendbc"]["provider"] == "opencode"
