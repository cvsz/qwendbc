from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
import uuid

from app.agentic.domain import (
    TaskEvent,
    TaskRecord,
    TaskStatus,
    validate_task_transition,
)


class TaskNotFound(LookupError):
    pass


class TaskStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _migrate(self) -> None:
        with self._connection:
            self._connection.executescript("""
                CREATE TABLE IF NOT EXISTS agentic_tasks (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    conversation_id TEXT,
                    agent_id TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_agentic_tasks_scope
                    ON agentic_tasks(tenant_id, principal_id, created_at);
                CREATE TABLE IF NOT EXISTS agentic_task_events (
                    id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL
                        REFERENCES agentic_tasks(id) ON DELETE CASCADE,
                    tenant_id TEXT NOT NULL,
                    principal_id TEXT NOT NULL,
                    previous_status TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_agentic_task_events_scope
                    ON agentic_task_events(
                        tenant_id,
                        principal_id,
                        task_id,
                        created_at
                    );
                """)

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> TaskRecord:
        return TaskRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            principal_id=row["principal_id"],
            conversation_id=row["conversation_id"],
            agent_id=row["agent_id"],
            objective=row["objective"],
            status=TaskStatus(row["status"]),
            correlation_id=row["correlation_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _append_event(
        self,
        task: TaskRecord,
        previous_status: TaskStatus | None,
    ) -> None:
        self._connection.execute(
            "INSERT INTO agentic_task_events("
            "id, task_id, tenant_id, principal_id, previous_status, status, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                task.id,
                task.tenant_id,
                task.principal_id,
                previous_status.value if previous_status is not None else None,
                task.status.value,
                task.updated_at,
            ),
        )

    def create(
        self,
        *,
        tenant_id: str,
        principal_id: str,
        conversation_id: str | None,
        agent_id: str,
        objective: str,
    ) -> TaskRecord:
        normalized_objective = objective.strip()
        if not normalized_objective:
            raise ValueError("objective must contain non-whitespace content")
        now = self._now()
        task = TaskRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            principal_id=principal_id,
            conversation_id=conversation_id,
            agent_id=agent_id,
            objective=normalized_objective,
            status=TaskStatus.CREATED,
            correlation_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
        )
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO agentic_tasks("
                "id, tenant_id, principal_id, conversation_id, agent_id, objective, "
                "status, correlation_id, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task.id,
                    task.tenant_id,
                    task.principal_id,
                    task.conversation_id,
                    task.agent_id,
                    task.objective,
                    task.status.value,
                    task.correlation_id,
                    task.created_at,
                    task.updated_at,
                ),
            )
            self._append_event(task, None)
        return task

    def get(
        self,
        tenant_id: str,
        principal_id: str,
        task_id: str,
    ) -> TaskRecord:
        row = self._connection.execute(
            "SELECT * FROM agentic_tasks "
            "WHERE id = ? AND tenant_id = ? AND principal_id = ?",
            (task_id, tenant_id, principal_id),
        ).fetchone()
        if row is None:
            raise TaskNotFound(task_id)
        return self._task_from_row(row)

    def list(
        self,
        tenant_id: str,
        principal_id: str,
    ) -> list[TaskRecord]:
        rows = self._connection.execute(
            "SELECT * FROM agentic_tasks "
            "WHERE tenant_id = ? AND principal_id = ? "
            "ORDER BY created_at, id",
            (tenant_id, principal_id),
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def transition(
        self,
        tenant_id: str,
        principal_id: str,
        task_id: str,
        target: TaskStatus,
    ) -> TaskRecord:
        with self._lock, self._connection:
            current = self.get(tenant_id, principal_id, task_id)
            validate_task_transition(current.status, target)
            now = self._now()
            self._connection.execute(
                "UPDATE agentic_tasks SET status = ?, updated_at = ? "
                "WHERE id = ? AND tenant_id = ? AND principal_id = ?",
                (
                    target.value,
                    now,
                    task_id,
                    tenant_id,
                    principal_id,
                ),
            )
            updated = self.get(tenant_id, principal_id, task_id)
            self._append_event(updated, current.status)
            return updated

    def events(
        self,
        tenant_id: str,
        principal_id: str,
        task_id: str,
    ) -> list[TaskEvent]:
        self.get(tenant_id, principal_id, task_id)
        rows = self._connection.execute(
            "SELECT * FROM agentic_task_events "
            "WHERE task_id = ? AND tenant_id = ? AND principal_id = ? "
            "ORDER BY created_at, id",
            (task_id, tenant_id, principal_id),
        ).fetchall()
        return [
            TaskEvent(
                id=row["id"],
                task_id=row["task_id"],
                tenant_id=row["tenant_id"],
                principal_id=row["principal_id"],
                previous_status=(
                    TaskStatus(row["previous_status"])
                    if row["previous_status"] is not None
                    else None
                ),
                status=TaskStatus(row["status"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()
