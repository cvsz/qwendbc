from __future__ import annotations

import hashlib
from pathlib import Path
import uuid


class WorkspacePathError(ValueError):
    pass


class WorkspaceFileTooLarge(ValueError):
    pass


class WorkspaceService:
    def __init__(self, root: str | Path, max_file_bytes: int = 1_000_000) -> None:
        self.root = Path(root).resolve()
        self.max_file_bytes = max_file_bytes
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _principal_namespace(principal_id: str) -> str:
        return hashlib.sha256(principal_id.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def _conversation_component(conversation_id: str) -> str:
        try:
            return str(uuid.UUID(conversation_id))
        except ValueError as exc:
            raise WorkspacePathError("Invalid conversation id") from exc

    def workspace_root(self, principal_id: str, conversation_id: str) -> Path:
        path = (
            self.root
            / self._principal_namespace(principal_id)
            / self._conversation_component(conversation_id)
        )
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve()

    def resolve(self, principal_id: str, conversation_id: str, relative_path: str) -> Path:
        requested = Path(relative_path)
        if requested.is_absolute():
            raise WorkspacePathError("Absolute paths are not allowed")
        root = self.workspace_root(principal_id, conversation_id)
        candidate = (root / requested).resolve(strict=False)
        if candidate != root and root not in candidate.parents:
            raise WorkspacePathError("Path escapes the conversation workspace")
        return candidate

    def write_text(
        self,
        principal_id: str,
        conversation_id: str,
        relative_path: str,
        content: str,
    ) -> None:
        encoded = content.encode("utf-8")
        if len(encoded) > self.max_file_bytes:
            raise WorkspaceFileTooLarge("Workspace file exceeds configured size limit")
        target = self.resolve(principal_id, conversation_id, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def read_text(self, principal_id: str, conversation_id: str, relative_path: str) -> str:
        target = self.resolve(principal_id, conversation_id, relative_path)
        data = target.read_bytes()
        if len(data) > self.max_file_bytes:
            raise WorkspaceFileTooLarge("Workspace file exceeds configured size limit")
        return data.decode("utf-8")

    def mkdir(self, principal_id: str, conversation_id: str, relative_path: str) -> None:
        self.resolve(principal_id, conversation_id, relative_path).mkdir(
            parents=True, exist_ok=True
        )

    def list_entries(
        self, principal_id: str, conversation_id: str, relative_path: str = "."
    ) -> list[dict[str, object]]:
        directory = self.resolve(principal_id, conversation_id, relative_path)
        if not directory.is_dir():
            raise NotADirectoryError(relative_path)
        root = self.workspace_root(principal_id, conversation_id)
        entries: list[dict[str, object]] = []
        for entry in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
            resolved = entry.resolve(strict=False)
            if resolved != root and root not in resolved.parents:
                continue
            entries.append(
                {
                    "name": entry.name,
                    "path": entry.relative_to(root).as_posix(),
                    "is_dir": entry.is_dir(),
                }
            )
        return entries
