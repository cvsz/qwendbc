from concurrent.futures import ThreadPoolExecutor
import hashlib

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.identity import PrincipalContext
from app.schemas.config import settings
from app.services.access_control import (
    guarded_remote_call,
    require_access,
    reset_access_control,
)


@pytest.fixture(autouse=True)
def reset_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "")
    monkeypatch.setattr(settings, "REMOTE_RATE_LIMIT_PER_MINUTE", 30)
    monkeypatch.setattr(settings, "REMOTE_MAX_CONCURRENT_REQUESTS", 4)
    reset_access_control()
    yield
    reset_access_control()


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_access)])
    def protected() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/identity")
    def identity(context: PrincipalContext = Depends(require_access)) -> dict[str, object]:
        return {
            "principal_id": context.principal_id,
            "tenant_id": context.tenant_id,
            "subject": context.subject,
            "roles": list(context.roles),
            "scopes": sorted(context.scopes),
            "authentication_method": context.authentication_method,
        }

    with TestClient(app) as test_client:
        yield test_client


def test_no_token_keeps_local_operation_compatible(client: TestClient) -> None:
    response = client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_local_identity_context_is_stable(client: TestClient) -> None:
    response = client.get("/identity")

    assert response.status_code == 200
    assert response.json() == {
        "principal_id": hashlib.sha256(b"local-access").hexdigest(),
        "tenant_id": "local",
        "subject": "local-operator",
        "roles": ["owner"],
        "scopes": ["*"],
        "authentication_method": "local",
    }


def test_verified_bearer_context_preserves_historical_principal_digest(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")
    authorization = "Bearer expected"

    response = client.get(
        "/identity",
        headers={
            "Authorization": authorization,
            "X-Tenant-ID": "attacker-tenant",
            "X-Roles": "admin,superuser",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["principal_id"] == hashlib.sha256(authorization.encode("utf-8")).hexdigest()
    assert body["tenant_id"] == "local"
    assert body["roles"] == ["owner"]
    assert body["authentication_method"] == "bearer"


def test_invalid_bearer_token_is_rejected(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")

    response = client.get("/protected", headers={"Authorization": "Bearer wrong"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_missing_bearer_token_is_rejected_when_access_token_is_configured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")

    response = client.get("/protected")

    assert response.status_code == 401


def test_rate_limit_returns_retry_after(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")
    monkeypatch.setattr(settings, "REMOTE_RATE_LIMIT_PER_MINUTE", 1)
    headers = {"Authorization": "Bearer expected"}

    assert client.get("/protected", headers=headers).status_code == 200
    limited = client.get("/protected", headers=headers)

    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) >= 1


def test_rate_limit_uses_the_trusted_proxy_address_when_enabled(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "QWENDBC_ACCESS_TOKEN", "expected")
    monkeypatch.setattr(settings, "REMOTE_RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    headers = {"Authorization": "Bearer expected"}

    first = client.get("/protected", headers={**headers, "X-Real-IP": "192.0.2.10"})
    second = client.get("/protected", headers={**headers, "X-Real-IP": "192.0.2.11"})

    assert first.status_code == 200
    assert second.status_code == 200


def test_remote_concurrency_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "REMOTE_MAX_CONCURRENT_REQUESTS", 1)

    with guarded_remote_call():
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lambda: guarded_remote_call().__enter__())
            with pytest.raises(HTTPException) as raised:
                future.result(timeout=1)

    assert raised.value.status_code == 429
