from pathlib import Path

import pytest

from app.agentic.domain import InvalidTaskTransition, TaskStatus
from app.agentic.task_store import TaskNotFound, TaskStore


def test_task_store_persists_and_reopens(tmp_path: Path) -> None:
    database = tmp_path / "agentic.sqlite3"
    store = TaskStore(database)
    task = store.create(
        tenant_id="tenant-a",
        principal_id="principal-a",
        conversation_id="conversation-a",
        agent_id="planner",
        objective="Plan the bounded task",
    )
    queued = store.transition(
        "tenant-a",
        "principal-a",
        task.id,
        TaskStatus.QUEUED,
    )
    store.close()

    reopened = TaskStore(database)
    persisted = reopened.get("tenant-a", "principal-a", task.id)
    events = reopened.events("tenant-a", "principal-a", task.id)

    assert queued.status is TaskStatus.QUEUED
    assert persisted.status is TaskStatus.QUEUED
    assert [event.status for event in events] == [
        TaskStatus.CREATED,
        TaskStatus.QUEUED,
    ]
    assert events[1].previous_status is TaskStatus.CREATED
    reopened.close()


def test_task_scope_prevents_cross_principal_access(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "agentic.sqlite3")
    task = store.create(
        tenant_id="tenant-a",
        principal_id="principal-a",
        conversation_id=None,
        agent_id="researcher",
        objective="Collect evidence",
    )

    with pytest.raises(TaskNotFound):
        store.get("tenant-a", "principal-b", task.id)

    with pytest.raises(TaskNotFound):
        store.get("tenant-b", "principal-a", task.id)

    store.close()


def test_invalid_and_terminal_transitions_fail_closed(tmp_path: Path) -> None:
    store = TaskStore(tmp_path / "agentic.sqlite3")
    task = store.create(
        tenant_id="tenant-a",
        principal_id="principal-a",
        conversation_id=None,
        agent_id="qa_verifier",
        objective="Verify evidence",
    )

    with pytest.raises(InvalidTaskTransition):
        store.transition(
            "tenant-a",
            "principal-a",
            task.id,
            TaskStatus.SUCCEEDED,
        )

    cancelled = store.transition(
        "tenant-a",
        "principal-a",
        task.id,
        TaskStatus.CANCELLED,
    )
    assert cancelled.status is TaskStatus.CANCELLED

    with pytest.raises(InvalidTaskTransition):
        store.transition(
            "tenant-a",
            "principal-a",
            task.id,
            TaskStatus.QUEUED,
        )

    store.close()
