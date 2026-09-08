import threading
from collections.abc import Generator
from typing import Any

import pytest

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


class PausingLock:
    """Real lock that pauses only its first successful acquisition."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pause_once = True
        self.entered = threading.Event()
        self.release = threading.Event()

    def __enter__(self) -> "PausingLock":
        self._lock.acquire()
        if self._pause_once:
            self._pause_once = False
            self.entered.set()
            if not self.release.wait(timeout=2):
                self._lock.release()
                raise TimeoutError("test gate was not released")
        return self

    def __exit__(self, *_: object) -> bool:
        self._lock.release()
        return False


class FakeModel:
    def __call__(self, **_: Any) -> dict[str, Any]:
        return {
            "choices": [{"text": "ok", "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }


def make_service(inference_lock: Any) -> LLMService:
    service = object.__new__(LLMService)
    service.model = FakeModel()  # type: ignore[assignment]
    service.model_path = "/tmp/test.gguf"
    service.is_loaded = True
    service._state_lock = threading.RLock()
    service._lifecycle_lock = threading.RLock()
    service._inference_lock = inference_lock
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

    with service._state_lock:
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

    with service._state_lock:
        service.model = None
        service.is_loaded = False
    gate.release.set()
    worker.join(timeout=2)

    assert not worker.is_alive()
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert str(errors[0]) == "Model not loaded"


def test_load_started_after_unload_transition_wins_lifecycle_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inference_lock = PausingLock()
    service = make_service(inference_lock)
    load_started = threading.Event()
    load_finished = threading.Event()
    load_result: list[bool] = []

    monkeypatch.setattr("app.services.llm_service.Llama", lambda **_: FakeModel())

    unload_worker = threading.Thread(target=service.unload_model)
    unload_worker.start()
    assert inference_lock.entered.wait(timeout=1)

    def run_load() -> None:
        load_started.set()
        load_result.append(service.load_model("/tmp/reloaded.gguf"))
        load_finished.set()

    load_worker = threading.Thread(target=run_load)
    load_worker.start()
    assert load_started.wait(timeout=1)

    # Unload already owns the lifecycle lock, so a later load must not return early
    # against the old loaded state. It should run only after unload completes.
    assert not load_finished.wait(timeout=0.1)

    inference_lock.release.set()
    unload_worker.join(timeout=2)
    load_worker.join(timeout=2)

    assert not unload_worker.is_alive()
    assert not load_worker.is_alive()
    assert load_result == [True]
    assert service.is_loaded is True
    assert service.model is not None
    assert service.model_path == "/tmp/reloaded.gguf"
