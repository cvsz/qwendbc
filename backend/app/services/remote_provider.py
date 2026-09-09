"""Reusable synchronous adapter for OpenAI-compatible remote providers."""

from collections.abc import Iterable, Iterator
from decimal import Decimal, InvalidOperation
import json
from typing import Any

import httpx

from app.services.provider_types import ProviderError, ProviderModel

_ROUTE_ALIASES = {
    "kilo": frozenset({"kilo-auto/free"}),
    "openrouter": frozenset({"openrouter/free"}),
}
_ALL_ROUTE_ALIASES = frozenset().union(*_ROUTE_ALIASES.values())
_OPENCODE_FREE_IDS = frozenset(
    {
        "big-pickle",
        "mimo-v2.5-free",
        "ling-3.0-flash-fin-free",
        "nemotron-3-ultra-free",
        "nemotron-3.5-lightning-free",
    }
)


class OpenAICompatibleProvider:
    """Bounded client for an OpenAI-compatible catalog and chat API."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        default_model: str,
        free_ids: Iterable[str],
        timeout_seconds: float,
        *,
        requires_api_key: bool = False,
    ) -> None:
        self.name = name.lower().strip()
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.requires_api_key = requires_api_key
        owned_aliases = _ROUTE_ALIASES.get(self.name, frozenset())
        self._configured_free_ids = frozenset(
            model
            for model in free_ids
            if model and (model not in _ALL_ROUTE_ALIASES or model in owned_aliases)
        )
        self._catalog: list[ProviderModel] | None = None

    def is_configured(self) -> bool:
        return bool(
            self.base_url
            and self.default_model
            and (not self.requires_api_key or self.api_key.strip())
        )

    @property
    def free_model_ids(self) -> frozenset[str]:
        catalog_ids = frozenset(model.id for model in self._catalog or [])
        provider_ids = _ROUTE_ALIASES.get(self.name, frozenset())
        return provider_ids | self._configured_free_ids | catalog_ids

    def list_models(self, refresh: bool = False) -> list[ProviderModel]:
        if self._catalog is not None and not refresh:
            return list(self._catalog)

        try:
            payload = self._get_json("/models")
        except json.JSONDecodeError:
            self._catalog = []
            return []
        entries = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            self._catalog = []
            return []

        models: list[ProviderModel] = []
        for entry in entries:
            model = self._normalize_model(entry)
            if model is not None:
                models.append(model)
        self._catalog = models
        return list(models)

    def complete(
        self,
        messages: list[dict[str, Any]],
        model: str | None,
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload = self._chat_payload(messages, model, temperature, top_p, max_tokens, stream=False)
        try:
            response = self._post_json("/chat/completions", payload)
        except ProviderError:
            raise
        except httpx.HTTPError as error:
            raise self._provider_error(error) from error
        if not isinstance(response, dict) or not isinstance(response.get("choices"), list):
            raise ProviderError("Provider returned an invalid completion response", retryable=True)
        return response

    def stream(
        self,
        messages: list[dict[str, Any]],
        model: str | None,
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> Iterator[dict[str, Any]]:
        payload = self._chat_payload(messages, model, temperature, top_p, max_tokens, stream=True)
        try:
            lines = self._stream_response("/chat/completions", payload)
            for raw_line in lines:
                line = raw_line.decode() if isinstance(raw_line, bytes) else raw_line
                if not isinstance(line, str) or not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if isinstance(chunk, dict) and isinstance(chunk.get("choices"), list):
                    yield chunk
        except ProviderError:
            raise
        except httpx.HTTPError as error:
            raise self._provider_error(error) from error

    def _normalize_model(self, entry: Any) -> ProviderModel | None:
        if not isinstance(entry, dict):
            return None
        model_id = entry.get("id")
        pricing = entry.get("pricing")
        architecture = entry.get("architecture")
        if (
            not isinstance(model_id, str)
            or not isinstance(pricing, dict)
            or not isinstance(architecture, dict)
        ):
            return None
        if not self._is_zero(pricing.get("prompt")) or not self._is_zero(pricing.get("completion")):
            return None
        modalities = architecture.get("output_modalities")
        text_modalities = (
            {modality for modality in modalities if isinstance(modality, str)}
            if isinstance(modalities, list)
            else set()
        )
        if "text" not in text_modalities:
            return None
        if self.name == "opencode" and model_id not in self._opencode_allowlist:
            return None
        name = entry.get("name")
        return ProviderModel(
            provider=self.name,
            id=model_id,
            name=name if isinstance(name, str) and name else model_id,
            free=True,
            context_length=(
                entry.get("context_length")
                if isinstance(entry.get("context_length"), int)
                else None
            ),
            prompt_price_per_token=float(pricing["prompt"]),
            completion_price_per_token=float(pricing["completion"]),
        )

    @property
    def _opencode_allowlist(self) -> frozenset[str]:
        return _OPENCODE_FREE_IDS | self._configured_free_ids

    @staticmethod
    def _is_zero(value: Any) -> bool:
        try:
            return Decimal(str(value)) == Decimal("0")
        except (InvalidOperation, ValueError):
            return False

    def _chat_payload(
        self,
        messages: list[dict[str, Any]],
        model: str | None,
        temperature: float,
        top_p: float,
        max_tokens: int,
        *,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "messages": messages,
            "model": self._resolve_model(model),
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def _resolve_model(self, requested_model: str | None) -> str:
        selected = requested_model or self.default_model
        if self.name != "opencode" or selected != "auto":
            return selected
        for candidate in self.list_models():
            if candidate.id in self._opencode_allowlist:
                return candidate.id
        raise ProviderError("No eligible free OpenCode model is available", retryable=True)

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _get_json(self, path: str) -> Any:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(self._url(path), headers=self._headers())
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as error:
            raise self._provider_error(error) from error

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(self._url(path), headers=self._headers(), json=payload)
                response.raise_for_status()
                decoded = response.json()
        except json.JSONDecodeError as error:
            raise ProviderError(
                "Provider returned an invalid completion response", retryable=True
            ) from error
        except httpx.HTTPError as error:
            raise self._provider_error(error) from error
        if not isinstance(decoded, dict):
            raise ProviderError("Provider returned an invalid completion response", retryable=True)
        return decoded

    def _stream_response(self, path: str, payload: dict[str, Any]) -> Iterator[str]:
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                with client.stream(
                    "POST", self._url(path), headers=self._headers(), json=payload
                ) as response:
                    response.raise_for_status()
                    yield from response.iter_lines()
        except httpx.HTTPError as error:
            raise self._provider_error(error) from error

    def _provider_error(self, error: httpx.HTTPError) -> ProviderError:
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            retryable = status_code == 429 or status_code >= 500
        else:
            retryable = True
        return ProviderError(f"{self.name} provider request failed", retryable=retryable)
