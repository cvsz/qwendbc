from pathlib import Path
import os
import pytest

from app.conversations.service import ConversationNotFound, ConversationService
from app.workspace.manager import WorkspacePathError, WorkspaceService


def test_conversation_persists_and_is_principal_scoped(tmp_path: Path):
    db = tmp_path / "cowork.sqlite3"
    first = ConversationService(db)
    conversation = first.create("principal-a", "Case review")
    first.append_event(
        "principal-a", conversation.id, "conversation.created", {"title": "Case review"}
    )
    first.close()

    reopened = ConversationService(db)
    loaded = reopened.get("principal-a", conversation.id)
    assert loaded.title == "Case review"
    assert [event.event_type for event in reopened.timeline("principal-a", conversation.id)] == [
        "conversation.created"
    ]
    with pytest.raises(ConversationNotFound):
        reopened.get("principal-b", conversation.id)
    reopened.close()


def test_workspace_confines_paths_and_persists_files(tmp_path: Path):
    service = WorkspaceService(tmp_path / "workspaces", max_file_bytes=1024)
    conversation_id = "8ef8db27-654b-4f24-b4ca-625183f6f6a4"
    service.write_text("principal-a", conversation_id, "notes/todo.txt", "safe")
    assert service.read_text("principal-a", conversation_id, "notes/todo.txt") == "safe"
    with pytest.raises(WorkspacePathError):
        service.write_text("principal-a", conversation_id, "../escape.txt", "nope")
    with pytest.raises(WorkspacePathError):
        service.read_text("principal-a", conversation_id, "/etc/passwd")


def test_workspace_rejects_symlink_escape(tmp_path: Path):
    if not hasattr(os, "symlink"):
        pytest.skip("symlink unsupported")
    service = WorkspaceService(tmp_path / "workspaces")
    conversation_id = "8ef8db27-654b-4f24-b4ca-625183f6f6a4"
    root = service.workspace_root("principal-a", conversation_id)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation not permitted")
    with pytest.raises(WorkspacePathError):
        service.write_text("principal-a", conversation_id, "link/pwned.txt", "nope")
