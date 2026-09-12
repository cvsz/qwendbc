from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    RETRYING = "retrying"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"


TERMINAL_TASK_STATUSES = frozenset(
    {
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.SUCCEEDED,
    }
)

_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.CREATED: frozenset({TaskStatus.QUEUED, TaskStatus.CANCELLED}),
    TaskStatus.QUEUED: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.WAITING_APPROVAL,
            TaskStatus.RETRYING,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.SUCCEEDED,
        }
    ),
    TaskStatus.WAITING_APPROVAL: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.RETRYING: frozenset(
        {
            TaskStatus.QUEUED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        }
    ),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
    TaskStatus.SUCCEEDED: frozenset(),
}


class InvalidTaskTransition(ValueError):
    pass


def validate_task_transition(
    current: TaskStatus,
    target: TaskStatus,
) -> None:
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidTaskTransition(
            f"Task transition {current.value} -> {target.value} is not allowed"
        )


@dataclass(frozen=True)
class AgentDefinition:
    id: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    approval_policy: str
    max_runtime_seconds: int
    max_steps: int


@dataclass(frozen=True)
class TaskRecord:
    id: str
    tenant_id: str
    principal_id: str
    conversation_id: str | None
    agent_id: str
    objective: str
    status: TaskStatus
    correlation_id: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TaskEvent:
    id: str
    task_id: str
    tenant_id: str
    principal_id: str
    previous_status: TaskStatus | None
    status: TaskStatus
    created_at: str
