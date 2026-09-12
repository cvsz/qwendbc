from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agentic import TaskStore, build_default_agent_registry
from app.routers.agentic import router
from app.schemas.config import Settings


def make_client(
    tmp_path: Path,
    token: str = "",
) -> tuple[TestClient, TaskStore]:
    app = FastAPI()
    app.state.settings = Settings(
        _env_file=None,
        QWENDBC_ACCESS_TOKEN=token,
    )
    app.state.agent_registry = build_default_agent_registry()
    store = TaskStore(tmp_path / "agentic.sqlite3")
    app.state.task_store = store
    app.include_router(router, prefix="/api/v1")
    return TestClient(app), store


def test_registry_is_authenticated_when_token_is_configured(
    tmp_path: Path,
) -> None:
    client, store = make_client(tmp_path, token="configured-token")

    denied = client.get("/api/v1/agents")
    allowed = client.get(
        "/api/v1/agents",
        headers={"Authorization": "Bearer configured-token"},
    )

    assert denied.status_code == 401
    assert allowed.status_code == 200
    ids = {agent["id"] for agent in allowed.json()}
    assert {
        "supervisor",
        "researcher",
        "planner",
        "coding_executor",
        "security_reviewer",
        "qa_verifier",
    }.issubset(ids)
    assert all(agent["allowed_tools"] == [] for agent in allowed.json())
    store.close()


def test_task_create_queue_cancel_and_events(tmp_path: Path) -> None:
    client, store = make_client(tmp_path)
    headers = {"Authorization": "Bearer principal-one"}

    created = client.post(
        "/api/v1/tasks",
        json={
            "agent_id": "planner",
            "objective": "Plan a safe implementation",
        },
        headers=headers,
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["status"] == "created"
    assert created.json()["tenant_id"] == "local"

    queued = client.post(
        f"/api/v1/tasks/{task_id}/queue",
        headers=headers,
    )
    assert queued.status_code == 200
    assert queued.json()["status"] == "queued"

    cancelled = client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    events = client.get(
        f"/api/v1/tasks/{task_id}/events",
        headers=headers,
    )
    assert events.status_code == 200
    assert [event["status"] for event in events.json()] == [
        "created",
        "queued",
        "cancelled",
    ]
    store.close()


def test_task_scope_blocks_other_local_principal(tmp_path: Path) -> None:
    client, store = make_client(tmp_path)
    first = {"Authorization": "Bearer principal-one"}
    second = {"Authorization": "Bearer principal-two"}

    task_id = client.post(
        "/api/v1/tasks",
        json={
            "agent_id": "researcher",
            "objective": "Collect source-backed evidence",
        },
        headers=first,
    ).json()["id"]

    assert client.get(f"/api/v1/tasks/{task_id}", headers=second).status_code == 404
    assert client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        headers=second,
    ).status_code == 404
    store.close()


def test_unknown_agent_is_rejected(tmp_path: Path) -> None:
    client, store = make_client(tmp_path)

    response = client.post(
        "/api/v1/tasks",
        json={
            "agent_id": "not-registered",
            "objective": "Do not run",
        },
    )

    assert response.status_code == 422
    store.close()
