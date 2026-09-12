from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
import uuid
from typing import Any


class ConversationNotFound(LookupError):
    pass


@dataclass(frozen=True)
class Conversation:
    id: str
    principal_id: str
    title: str
    created_at: str


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    conversation_id: str
    principal_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: str


class ConversationService:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_conversations_principal
                    ON conversations(principal_id, created_at);
                CREATE TABLE IF NOT EXISTS timeline_events (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    principal_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_timeline_conversation
                    ON timeline_events(principal_id, conversation_id, created_at);
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def create(self, principal_id: str, title: str) -> Conversation:
        item = Conversation(
            str(uuid.uuid4()),
            principal_id,
            title.strip() or "New conversation",
            self._now(),
        )
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO conversations(id, principal_id, title, created_at) "
                "VALUES (?, ?, ?, ?)",
                (item.id, item.principal_id, item.title, item.created_at),
            )
        return item

    def get(self, principal_id: str, conversation_id: str) -> Conversation:
        row = self._connection.execute(
            "SELECT id, principal_id, title, created_at FROM conversations "
            "WHERE id = ? AND principal_id = ?",
            (conversation_id, principal_id),
        ).fetchone()
        if row is None:
            raise ConversationNotFound(conversation_id)
        return Conversation(**dict(row))

    def append_event(
        self,
        principal_id: str,
        conversation_id: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> TimelineEvent:
        self.get(principal_id, conversation_id)
        event = TimelineEvent(
            str(uuid.uuid4()),
            conversation_id,
            principal_id,
            event_type,
            payload,
            self._now(),
        )
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO timeline_events("
                "id, conversation_id, principal_id, event_type, payload_json, created_at"
                ") VALUES (?, ?, ?, ?, ?, ?)",
                (
                    event.id,
                    event.conversation_id,
                    event.principal_id,
                    event.event_type,
                    json.dumps(payload, separators=(",", ":"), sort_keys=True),
                    event.created_at,
                ),
            )
        return event

    def timeline(self, principal_id: str, conversation_id: str) -> list[TimelineEvent]:
        self.get(principal_id, conversation_id)
        rows = self._connection.execute(
            "SELECT id, conversation_id, principal_id, event_type, payload_json, created_at "
            "FROM timeline_events WHERE conversation_id = ? AND principal_id = ? "
            "ORDER BY created_at, id",
            (conversation_id, principal_id),
        ).fetchall()
        return [
            TimelineEvent(
                id=row["id"],
                conversation_id=row["conversation_id"],
                principal_id=row["principal_id"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()
