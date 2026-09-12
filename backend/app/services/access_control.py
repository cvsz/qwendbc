"""Application access checks and process-local remote-provider limits."""

from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import hmac
import ipaddress
import threading
import time

from fastapi import HTTPException, Request, status

from app.identity import PrincipalContext, build_local_principal_context
from app.schemas.config import Settings, settings

_WINDOW_SECONDS = 60.0
_MAX_CLIENTS = 4_096
_state_lock = threading.RLock()
_request_windows: OrderedDict[str, tuple[float, int]] = OrderedDict()
_remote_limit = settings.REMOTE_MAX_CONCURRENT_REQUESTS
_remote_semaphore = threading.BoundedSemaphore(_remote_limit)


def _too_many_requests(retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Request limit exceeded",
        headers={"Retry-After": str(max(1, retry_after))},
    )


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _client_key(request: Request, token: str, config: Settings) -> str:
    host = request.client.host if request.client is not None else "unknown"
    if config.TRUST_PROXY_HEADERS:
        forwarded_host = request.headers.get("X-Real-IP", "").strip()
        try:
            host = str(ipaddress.ip_address(forwarded_host))
        except ValueError:
            pass
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{token_hash}:{host}"


def _check_fixed_window(key: str, limit: int) -> None:
    now = time.monotonic()
    with _state_lock:
        expired = [
            client_key
            for client_key, (window_start, _) in _request_windows.items()
            if now - window_start >= _WINDOW_SECONDS
        ]
        for client_key in expired:
            del _request_windows[client_key]

        window_start, count = _request_windows.get(key, (now, 0))
        if now - window_start >= _WINDOW_SECONDS:
            window_start, count = now, 0
        if count >= limit:
            raise _too_many_requests(int(_WINDOW_SECONDS - (now - window_start)) + 1)

        _request_windows[key] = (window_start, count + 1)
        _request_windows.move_to_end(key)
        while len(_request_windows) > _MAX_CLIENTS:
            _request_windows.popitem(last=False)


def _request_settings(request: Request) -> Settings:
    configured = getattr(request.app.state, "settings", settings)
    return configured if isinstance(configured, Settings) else settings


def require_access(request: Request) -> PrincipalContext:
    """Authenticate the request and return its explicit local principal context.

    Existing callers may ignore the return value. Cowork and future policy
    surfaces should consume it instead of deriving identity from headers again.
    """

    config = _request_settings(request)
    expected = config.QWENDBC_ACCESS_TOKEN
    authorization = request.headers.get("Authorization", "")

    if not expected:
        return build_local_principal_context(
            authorization,
            bearer_verified=False,
        )

    scheme, _, presented = authorization.partition(" ")
    if (
        scheme.lower() != "bearer"
        or not presented
        or not hmac.compare_digest(presented, expected)
    ):
        raise _unauthorized()
    _check_fixed_window(
        _client_key(request, expected, config),
        config.REMOTE_RATE_LIMIT_PER_MINUTE,
    )
    return build_local_principal_context(
        authorization,
        bearer_verified=True,
    )


def _semaphore(config: Settings = settings) -> threading.BoundedSemaphore:
    global _remote_limit, _remote_semaphore
    configured_limit = config.REMOTE_MAX_CONCURRENT_REQUESTS
    with _state_lock:
        if configured_limit != _remote_limit:
            _remote_limit = configured_limit
            _remote_semaphore = threading.BoundedSemaphore(configured_limit)
        return _remote_semaphore


class RemoteCallLease:
    """Idempotently releasable reservation for a remote-provider call."""

    def __init__(self, config: Settings = settings) -> None:
        self._semaphore = _semaphore(config)
        self._released = False
        if not self._semaphore.acquire(blocking=False):
            raise _too_many_requests(1)

    def release(self) -> None:
        with _state_lock:
            if self._released:
                return
            self._released = True
        self._semaphore.release()

    def __enter__(self) -> "RemoteCallLease":
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def reserve_remote_call(config: Settings = settings) -> RemoteCallLease:
    """Reserve remote capacity before a streaming response is opened."""
    return RemoteCallLease(config)


@contextmanager
def guarded_remote_call(config: Settings = settings) -> Iterator[None]:
    """Reserve bounded remote capacity without ever blocking local inference."""
    lease = reserve_remote_call(config)
    try:
        yield
    finally:
        lease.release()


def reset_access_control() -> None:
    """Clear process-local accounting; intended for in-process test isolation."""
    global _remote_limit, _remote_semaphore
    with _state_lock:
        _request_windows.clear()
        _remote_limit = settings.REMOTE_MAX_CONCURRENT_REQUESTS
        _remote_semaphore = threading.BoundedSemaphore(_remote_limit)
