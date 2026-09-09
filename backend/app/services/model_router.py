"""Routing between the local model service and approved free remote providers."""

from collections.abc import Iterator
from datetime import datetime, timezone
import time
import uuid
from typing import Any

from fastapi import HTTPException

from app.schemas.chat import ModelCatalogItem, ModelsResponse, ProviderStatus
from app.schemas.config import Settings, settings
from app.services.access_control import guarded_remote_call
from app.services.provider_types import ProviderError, ProviderModel
from app.services.remote_provider import OpenAICompatibleProvider

_CATALOG_TTL_SECONDS = 30.0


class ModelRouter:
    """Use configured free remote providers before the loaded local service."""

    def __init__(
        self,
        local_service: Any,
        config: Settings = settings,
        providers: list[Any] | None = None,
    ) -> None:
        self.local_service = local_service
        self.config = config
        self.providers = providers if providers is not None else self._build_providers()
        self._catalog_cache: dict[str, tuple[float, list[ProviderModel]]] = {}
        self._catalog_cached_at: dict[str, datetime] = {}

    def _build_providers(self) -> list[OpenAICompatibleProvider]:
        return [
            OpenAICompatibleProvider(
                "kilo",
                self.config.KILO_BASE_URL,
                self.config.KILO_API_KEY,
                self.config.KILO_MODEL,
                (),
                self.config.REMOTE_REQUEST_TIMEOUT_SECONDS,
            ),
            OpenAICompatibleProvider(
                "opencode",
                self.config.OPENCODE_BASE_URL,
                self.config.OPENCODE_API_KEY,
                self.config.OPENCODE_FREE_MODEL,
                (),
                self.config.REMOTE_REQUEST_TIMEOUT_SECONDS,
                requires_api_key=True,
            ),
            OpenAICompatibleProvider(
                "openrouter",
                self.config.OPENROUTER_BASE_URL,
                self.config.OPENROUTER_API_KEY,
                self.config.OPENROUTER_MODEL,
                (),
                self.config.REMOTE_REQUEST_TIMEOUT_SECONDS,
                requires_api_key=True,
            ),
        ]

    @property
    def _remote_enabled(self) -> bool:
        return self.config.MODEL_MODE == "auto_free" and self.config.REMOTE_MODELS_ENABLED

    def _provider_by_name(self, name: str) -> Any | None:
        return next((item for item in self.providers if item.name == name), None)

    def _provider_statuses(self) -> list[ProviderStatus]:
        statuses: list[ProviderStatus] = []
        for name in self.config.free_provider_order:
            if name == "local":
                statuses.append(
                    ProviderStatus(
                        name="local",
                        configured=True,
                        available=bool(self.local_service.is_loaded),
                    )
                )
                continue
            provider = self._provider_by_name(name)
            configured = bool(provider and self._remote_enabled and provider.is_configured())
            statuses.append(ProviderStatus(name=name, configured=configured, available=configured))
        return statuses

    def provider_statuses(self) -> list[ProviderStatus]:
        """Return non-secret provider availability without querying remote catalogs."""
        return self._provider_statuses()

    def _catalog_for(self, provider: Any, refresh: bool) -> list[ProviderModel]:
        cached = self._catalog_cache.get(provider.name)
        if cached and not refresh and time.monotonic() - cached[0] < _CATALOG_TTL_SECONDS:
            return list(cached[1])
        try:
            models = provider.list_models(refresh=refresh or cached is not None)
        except ProviderError:
            models = []
        self._catalog_cache[provider.name] = (time.monotonic(), list(models))
        self._catalog_cached_at[provider.name] = datetime.now(timezone.utc)
        return list(models)

    def list_models(self, refresh: bool = False) -> ModelsResponse:
        data: list[ModelCatalogItem] = []
        for status in self._provider_statuses():
            if status.name == "local":
                data.append(
                    ModelCatalogItem(
                        id=str(self.local_service.get_model_info()["name"]),
                        name=str(self.local_service.get_model_info()["name"]),
                        provider="local",
                        free=True,
                        supports_chat=True,
                        context_length=self.local_service.get_model_info()["context_length"],
                    )
                )
                continue
            provider = self._provider_by_name(status.name)
            if not status.configured or provider is None:
                continue
            for model in self._catalog_for(provider, refresh):
                data.append(
                    ModelCatalogItem(
                        id=model.id,
                        name=model.name,
                        provider=model.provider,
                        free=model.free,
                        supports_chat=model.supports_chat,
                        context_length=model.context_length,
                    )
                )
        return ModelsResponse(
            data=data,
            providers=self._provider_statuses(),
            cached_at=max(
                self._catalog_cached_at.values(),
                default=datetime.now(timezone.utc),
            ),
        )

    def get_model_info(self) -> dict[str, Any]:
        info = dict(self.local_service.get_model_info())
        info["providers"] = [status.model_dump() for status in self._provider_statuses()]
        info.update(self.routing_state())
        return info

    def routing_state(self) -> dict[str, Any]:
        """Return the current non-secret route and fallback state."""
        statuses = self._provider_statuses()
        active = next((status for status in statuses if status.available), None)
        selected_model: str | None = None
        if active is not None:
            if active.name == "local":
                selected_model = str(self.local_service.get_model_info()["name"])
            else:
                provider = self._provider_by_name(active.name)
                if provider is not None:
                    selected_model = str(provider.default_model)
        return {
            "active_provider": active.name if active is not None else None,
            "selected_model": selected_model,
            "remote_models_enabled": self._remote_enabled,
            "fallback_available": bool(self.local_service.is_loaded),
        }

    def validate_request(self, provider: str | None = None, model: str | None = None) -> None:
        """Validate that a request has at least one route before opening a stream."""
        selections = self._selection(provider, model)
        if not any(name != "local" or self.local_service.is_loaded for name, _, _ in selections):
            raise RuntimeError("Model not loaded")

    def _is_eligible(self, provider: Any, model: str) -> bool:
        if model in provider.free_model_ids:
            return True
        for item in self._catalog_for(provider, refresh=False):
            if item.id == model:
                return item.free and item.supports_chat
        return False

    def _is_eligible_or_dynamic_default(self, provider: Any, model: str) -> bool:
        return provider.name == "opencode" and model == "auto" or self._is_eligible(provider, model)

    def _selection(
        self, provider: str | None, model: str | None
    ) -> list[tuple[str, Any | None, str | None]]:
        if provider == "local":
            local_name = str(self.local_service.get_model_info()["name"])
            if model is not None and model != local_name:
                raise ValueError("Requested local model is not available")
            return [("local", None, local_name)]

        if provider:
            selected = self._provider_by_name(provider)
            if selected is None or not self._remote_enabled or not selected.is_configured():
                raise ValueError("Requested provider is disabled")
            selected_model = model or selected.default_model
            if not self._is_eligible_or_dynamic_default(selected, selected_model):
                raise ValueError("Requested model is not an eligible free text model")
            return [(provider, selected, selected_model)]

        if model:
            for candidate in self.providers:
                if (
                    self._remote_enabled
                    and candidate.is_configured()
                    and self._is_eligible(candidate, model)
                ):
                    return [(candidate.name, candidate, model)]
            local_name = str(self.local_service.get_model_info()["name"])
            if model == local_name:
                return [("local", None, local_name)]
            raise ValueError("Requested model is not an eligible free text model")

        selections: list[tuple[str, Any | None, str | None]] = []
        for name in self.config.free_provider_order:
            if name == "local":
                selections.append(("local", None, None))
                continue
            selected = self._provider_by_name(name)
            if (
                self._remote_enabled
                and selected is not None
                and selected.is_configured()
                and self._is_eligible_or_dynamic_default(selected, selected.default_model)
            ):
                selections.append((name, selected, None))
        return selections

    def _decorate(
        self,
        response: dict[str, Any],
        provider: str,
        model: str,
        fallback: bool,
        rag_sources: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        result = dict(response)
        result.setdefault("id", f"chatcmpl-{uuid.uuid4().hex}")
        result.setdefault("object", "chat.completion")
        result.setdefault("created", int(time.time()))
        result["model"] = model
        result.setdefault("choices", [])
        result.setdefault("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        metadata: dict[str, Any] = {"provider": provider, "model": model, "fallback": fallback}
        if rag_sources:
            metadata["rag_sources"] = [
                {
                    "id": source.get("id"),
                    "filename": source.get("metadata", {}).get("filename"),
                    "distance": source.get("distance"),
                }
                for source in rag_sources
            ]
        result["qwendbc"] = metadata
        return result

    def complete(
        self,
        messages: list[dict[str, Any]],
        provider: str | None = None,
        model: str | None = None,
        temperature: float = settings.TEMPERATURE,
        top_p: float = settings.TOP_P,
        max_tokens: int = settings.MAX_TOKENS,
        rag_sources: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        selections = self._selection(provider, model)
        last_error: ProviderError | None = None
        for attempt, (name, selected, selected_model) in enumerate(selections):
            try:
                if name == "local":
                    if not self.local_service.is_loaded:
                        continue
                    response = self.local_service.generate(
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                    )
                    response_model = str(
                        response.get("model") or self.local_service.get_model_info()["name"]
                    )
                else:
                    assert selected is not None
                    with guarded_remote_call():
                        response = selected.complete(
                            messages=messages,
                            model=selected_model,
                            temperature=temperature,
                            top_p=top_p,
                            max_tokens=max_tokens,
                        )
                    response_model = str(
                        response.get("model") or selected_model or selected.default_model
                    )
                return self._decorate(response, name, response_model, attempt > 0, rag_sources)
            except ProviderError as error:
                last_error = error
            except HTTPException:
                raise
            except Exception:
                last_error = ProviderError("Free model provider is unavailable", retryable=True)
        if not self.local_service.is_loaded:
            raise RuntimeError("Model not loaded")
        raise last_error or ProviderError("No free model provider is available", retryable=True)

    def stream(
        self,
        messages: list[dict[str, Any]],
        provider: str | None = None,
        model: str | None = None,
        temperature: float = settings.TEMPERATURE,
        top_p: float = settings.TOP_P,
        max_tokens: int = settings.MAX_TOKENS,
    ) -> Iterator[dict[str, Any]]:
        selections = self._selection(provider, model)
        last_error: ProviderError | None = None
        for name, selected, selected_model in selections:
            emitted_content = False
            try:
                if name == "local":
                    if not self.local_service.is_loaded:
                        continue
                    stream = self.local_service.generate_stream(
                        messages=messages,
                        temperature=temperature,
                        top_p=top_p,
                        max_tokens=max_tokens,
                    )
                    for chunk in stream:
                        emitted_content = emitted_content or self._has_content(chunk)
                        yield chunk
                else:
                    assert selected is not None
                    with guarded_remote_call():
                        for chunk in selected.stream(
                            messages=messages,
                            model=selected_model,
                            temperature=temperature,
                            top_p=top_p,
                            max_tokens=max_tokens,
                        ):
                            emitted_content = emitted_content or self._has_content(chunk)
                            yield chunk
                return
            except ProviderError as error:
                if emitted_content:
                    raise error
                last_error = error
            except HTTPException:
                raise
            except Exception:
                fallback_error = ProviderError("Free model provider is unavailable", retryable=True)
                if emitted_content:
                    raise fallback_error
                last_error = fallback_error
        if not self.local_service.is_loaded:
            raise RuntimeError("Model not loaded")
        raise last_error or ProviderError("No free model provider is available", retryable=True)

    @staticmethod
    def _has_content(chunk: dict[str, Any]) -> bool:
        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            return False
        delta = choices[0].get("delta")
        return isinstance(delta, dict) and bool(delta.get("content"))
