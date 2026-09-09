from collections.abc import Iterable
from typing import Any

import httpx
import pytest

from app.services.provider_types import ProviderError
from app.services.remote_provider import OpenAICompatibleProvider


def make_provider(
    name: str,
    base_url: str,
    *,
    default_model: str,
    api_key: str = "",
    free_ids: Iterable[str] = (),
) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        name=name,
        base_url=base_url,
        api_key=api_key,
        default_model=default_model,
        free_ids=free_ids,
        timeout_seconds=12,
    )


def test_kilo_catalog_keeps_only_free_text_models(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda _: {
            "data": [
                {
                    "id": "stepfun/step-3.7-flash:free",
                    "name": "Step",
                    "pricing": {"prompt": "0", "completion": "0"},
                    "architecture": {"output_modalities": ["text"]},
                },
                {
                    "id": "paid/model",
                    "name": "Paid",
                    "pricing": {"prompt": "1", "completion": "1"},
                    "architecture": {"output_modalities": ["text"]},
                },
                {
                    "id": "google/lyria-3-pro-preview",
                    "name": "Audio",
                    "pricing": {"prompt": "0", "completion": "0"},
                    "architecture": {"output_modalities": ["audio"]},
                },
            ]
        },
    )

    assert [model.id for model in provider.list_models(refresh=True)] == [
        "stepfun/step-3.7-flash:free"
    ]


def test_catalog_accepts_raw_arrays_and_returns_empty_for_malformed_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = make_provider("openrouter", "https://router.test", default_model="openrouter/free")
    monkeypatch.setattr(provider, "_get_json", lambda _: [{"id": "not-enough-metadata"}])

    assert provider.list_models(refresh=True) == []

    monkeypatch.setattr(provider, "_get_json", lambda _: {"unexpected": []})
    assert provider.list_models(refresh=True) == []


def test_route_aliases_belong_only_to_their_own_provider() -> None:
    kilo = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    router = make_provider("openrouter", "https://router.test", default_model="openrouter/free")
    opencode = make_provider("opencode", "https://opencode.test", default_model="auto")

    assert "kilo-auto/free" in kilo.free_model_ids
    assert "openrouter/free" not in kilo.free_model_ids
    assert "openrouter/free" in router.free_model_ids
    assert "kilo-auto/free" not in router.free_model_ids
    assert "kilo-auto/free" not in opencode.free_model_ids
    assert "openrouter/free" not in opencode.free_model_ids


def test_caller_supplied_free_ids_cannot_cross_provider_route_alias_ownership() -> None:
    provider = make_provider(
        "kilo",
        "https://kilo.test",
        default_model="kilo-auto/free",
        free_ids=("openrouter/free", "community/free"),
    )

    assert provider.free_model_ids == frozenset({"kilo-auto/free", "community/free"})


def test_opencode_auto_resolves_first_catalog_model_in_its_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = make_provider("opencode", "https://opencode.test", default_model="auto")
    captured: dict[str, Any] = {}
    monkeypatch.setattr(
        provider,
        "_get_json",
        lambda _: {
            "data": [
                {
                    "id": "paid/model",
                    "name": "Paid",
                    "pricing": {"prompt": "0", "completion": "0"},
                    "architecture": {"output_modalities": ["text"]},
                },
                {
                    "id": "mimo-v2.5-free",
                    "name": "MiMo",
                    "pricing": {"prompt": "0.0", "completion": 0},
                    "architecture": {"output_modalities": ["text"]},
                },
            ]
        },
    )

    def post(_: str, payload: dict[str, Any]) -> dict[str, Any]:
        captured["model"] = payload["model"]
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(provider, "_post_json", post)

    provider.complete([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32)

    assert captured == {"model": "mimo-v2.5-free"}


def test_complete_sends_openai_compatible_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("openrouter", "https://router.test", default_model="openrouter/free")
    captured: dict[str, Any] = {}
    response = {
        "id": "x",
        "model": "openrouter/free",
        "choices": [{"message": {"content": "ok"}}],
        "usage": {},
    }

    def post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
        captured.update(path=path, payload=payload)
        return response

    monkeypatch.setattr(provider, "_post_json", post)
    result = provider.complete([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32)

    assert result["choices"][0]["message"]["content"] == "ok"
    assert captured == {
        "path": "/chat/completions",
        "payload": {
            "messages": [{"role": "user", "content": "hi"}],
            "model": "openrouter/free",
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 32,
            "stream": False,
        },
    }


def test_complete_rejects_missing_choices_with_safe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    monkeypatch.setattr(provider, "_post_json", lambda *_: {"id": "unexpected"})

    with pytest.raises(ProviderError, match="invalid completion response") as raised:
        provider.complete([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32)

    assert raised.value.retryable is True


def test_http_429_is_retryable_and_401_is_not(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    request = httpx.Request("POST", "https://kilo.test/chat/completions")

    for status_code, retryable in ((429, True), (401, False)):
        response = httpx.Response(status_code, request=request, content=b"sensitive upstream body")
        error = httpx.HTTPStatusError("upstream failure", request=request, response=response)
        monkeypatch.setattr(
            provider, "_post_json", lambda *_args, error=error: (_ for _ in ()).throw(error)
        )

        with pytest.raises(ProviderError) as raised:
            provider.complete([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32)

        assert raised.value.retryable is retryable
        assert "sensitive" not in str(raised.value)


def test_timeout_becomes_retryable_safe_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    monkeypatch.setattr(
        provider,
        "_post_json",
        lambda *_: (_ for _ in ()).throw(httpx.TimeoutException("do not expose this detail")),
    )

    with pytest.raises(ProviderError) as raised:
        provider.complete([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32)

    assert raised.value.retryable is True
    assert "detail" not in str(raised.value)


def test_stream_parses_data_lines_until_done(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = make_provider("kilo", "https://kilo.test", default_model="kilo-auto/free")
    monkeypatch.setattr(
        provider,
        "_stream_response",
        lambda *_: [
            ": keepalive",
            "",
            'data: {"choices":[{"delta":{"content":"hi"}}]}',
            "data: [DONE]",
            'data: {"choices":[{"delta":{"content":"ignored"}}]}',
        ],
    )

    chunks = list(provider.stream([{"role": "user", "content": "hi"}], None, 0.7, 0.9, 32))

    assert chunks == [{"choices": [{"delta": {"content": "hi"}}]}]
