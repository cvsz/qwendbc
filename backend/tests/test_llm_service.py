import threading
from collections.abc import Generator
from typing import Any

from app.services.llm_service import LLMService


class GateLock:
    """Pause lock entry so tests can deterministically change service state."""

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()

    def __enter__(self) -> "GateLock":
        self.entered.set()
        if not self.release.wait(timeout=2):
            raise TimeoutError("test gate was not released")
        return self

    def __exit__(self, *_: object) -> bool:
        return False


class FakeModel:
    def __call__(self, **_: Any) -> dict[str, Any]:
        return {
            "choices": [{"text": "ok", "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }


def make_service(gate: GateLock) -> LLMService:
    service = object.__new__(LLMService)
    service.model = FakeModel()  # type: ignore[assignment]
    service.model_path = "/tmp/test.gguf"
    service.is_loaded = True
    service._inference_lock = gate
    return service


def test_generate_rechecks_loaded_state_after_acquiring_inference_lock() -> None:
    gate = GateLock()
    service = make_service(gate)
    errors: list[Exception] = []

    def run() -> None:
        try:
            service.generate([{"role": "user", "content": "hello"}], max_tokens=1)
        except Exception as exc:  # noqa: BLE001 - test captures the exact failure type
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    assert gate.entered.wait(timeout=1)

    service.model = None
    service.is_loaded = False
    gate.release.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert str(errors[0]) == "Model not loaded"


def test_stream_rechecks_loaded_state_after_acquiring_inference_lock() -> None:
    gate = GateLock()
    service = make_service(gate)
    errors: list[Exception] = []

    def run() -> None:
        stream: Generator[dict[str, Any], None, None] = service.generate_stream(
            [{"role": "user", "content": "hello"}],
            max_tokens=1,
        )
        try:
            next(stream)
        except Exception as exc:  # noqa: BLE001 - test captures the exact failure type
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    assert gate.entered.wait(timeout=1)

    service.model = None
    service.is_loaded = False
    gate.release.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert str(errors[0]) == "Model not loaded"
