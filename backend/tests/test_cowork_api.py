from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.conversations.service import ConversationService
from app.routers.cowork import router
from app.schemas.config import Settings
from app.workspace.manager import WorkspaceService


def make_client(tmp_path: Path, token: str = "a" * 32) -> TestClient:
    app = FastAPI()
    app.state.settings = Settings(
        _env_file=None,
        QWENDBC_ACCESS_TOKEN=token,
    )
    app.state.conversation_service = ConversationService(tmp_path / "cowork.sqlite3")
    app.state.workspace_service = WorkspaceService(tmp_path / "workspaces")
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def test_cowork_api_requires_bearer_and_records_timeline(tmp_path: Path):
    client = make_client(tmp_path)
    assert client.post("/api/v1/conversations", json={"title": "Case"}).status_code == 401
    headers = {"Authorization": f"Bearer {'a' * 32}"}
    created = client.post(
        "/api/v1/conversations",
        json={"title": "Case"},
        headers=headers,
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]
    write = client.put(
        f"/api/v1/conversations/{conversation_id}/workspace/file",
        json={"path": "notes/a.txt", "content": "hello"},
        headers=headers,
    )
    assert write.status_code == 204
    read = client.get(
        f"/api/v1/conversations/{conversation_id}/workspace/file",
        params={"path": "notes/a.txt"},
        headers=headers,
    )
    assert read.json() == {"path": "notes/a.txt", "content": "hello"}
    events = client.get(
        f"/api/v1/conversations/{conversation_id}/timeline",
        headers=headers,
    ).json()
    assert [event["event_type"] for event in events] == [
        "conversation.created",
        "workspace.file.written",
        "workspace.file.read",
    ]


def test_different_local_principals_cannot_access_conversation(tmp_path: Path):
    client = make_client(tmp_path, token="")
    first = {"Authorization": "Bearer principal-one"}
    second = {"Authorization": "Bearer principal-two"}
    created = client.post(
        "/api/v1/conversations",
        json={"title": "Private"},
        headers=first,
    )
    conversation_id = created.json()["id"]
    response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=second,
    )
    assert response.status_code == 404


def test_api_rejects_workspace_traversal(tmp_path: Path):
    client = make_client(tmp_path)
    headers = {"Authorization": f"Bearer {'a' * 32}"}
    conversation_id = client.post(
        "/api/v1/conversations",
        json={},
        headers=headers,
    ).json()["id"]
    response = client.put(
        f"/api/v1/conversations/{conversation_id}/workspace/file",
        json={"path": "../escape.txt", "content": "nope"},
        headers=headers,
    )
    assert response.status_code == 400
