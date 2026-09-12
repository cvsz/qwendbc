# AionUi Cowork Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first AI-DBC-native Cowork vertical slice: durable conversations, per-principal confined workspaces, structured timeline events, and authenticated FastAPI endpoints without changing legacy chat/RAG behavior.

**Architecture:** Keep all new Python packages under `backend/app`. Persist conversation/timeline metadata in a separate SQLite database and place files beneath a configured workspace root namespaced by credential principal plus conversation UUID. Reuse the existing `require_access` bearer gate and mount the Cowork router alongside the existing chat/documents routers.

**Tech Stack:** Python 3, FastAPI, Pydantic, stdlib `sqlite3`, `pathlib`, pytest.

**Spec:** `docs/AIONUI_PORT_PLAN.md`

## Global Constraints

- Preserve existing `/api/v1/chat/completions` behavior.
- Preserve local RAG and local inference behavior.
- Provider credentials remain server-side.
- Filesystem operations must be confined to the configured workspace root.
- Protected remote operations reuse the existing bearer-token gate.
- No ACP, shell/process tools, network tools, scheduler, or unattended automation in this slice.
- New AI-DBC-native source stays under the repository license; copied Apache-2.0 upstream source would require preserved notices. This slice contains no copied AionUi source.

---

### Task 1: Conversation and timeline persistence

**Files:**
- Create: `backend/app/conversations/service.py`
- Test: `backend/tests/test_cowork_domain.py`

**Interfaces:**
- Produces: `ConversationService.create()`, `get()`, `append_event()`, `timeline()`, `close()`.
- Produces: `Conversation`, `TimelineEvent`, `ConversationNotFound`.

- [x] Write a persistence regression that creates a conversation/event, closes the SQLite connection, reopens it, and proves the same principal can load it.
- [x] Add a cross-principal regression that returns `ConversationNotFound` for the same conversation ID under a different principal.
- [x] Run the focused test before implementation and observe failure because `app.conversations.service` does not exist.
- [x] Implement the minimal SQLite schema and service methods.
- [x] Re-run the focused tests and observe green.

### Task 2: Confined workspace service

**Files:**
- Create: `backend/app/workspace/manager.py`
- Test: `backend/tests/test_cowork_domain.py`

**Interfaces:**
- Produces: `WorkspaceService.workspace_root()`, `resolve()`, `write_text()`, `read_text()`, `mkdir()`, `list_entries()`.
- Produces: `WorkspacePathError`, `WorkspaceFileTooLarge`.

- [x] Add traversal tests for `../escape.txt` and an absolute path.
- [x] Add a symlink-escape regression.
- [x] Namespace workspace roots by SHA-256 of the principal credential material and validated conversation UUID.
- [x] Resolve paths with `Path.resolve(strict=False)` and reject any result outside the conversation root.
- [x] Add byte bounds for text reads/writes.

### Task 3: Authenticated Cowork API

**Files:**
- Create: `backend/app/schemas/cowork.py`
- Create: `backend/app/routers/cowork.py`
- Test: `backend/tests/test_cowork_api.py`

**Interfaces:**
- Consumes: existing `app.services.access_control.require_access`.
- Produces: `/api/v1/conversations`, `/timeline`, and `/workspace` endpoints.

- [x] Add a regression proving requests without the configured bearer token receive 401.
- [x] Add a regression proving a different credential principal cannot fetch another principal's conversation.
- [x] Add workspace write/read API tests and assert corresponding timeline event types.
- [x] Add traversal rejection at the HTTP boundary.
- [x] Implement route handlers without adding ACP/shell/network/scheduler behavior.

### Task 4: Repository integration

**Files:**
- Modify: `backend/app/schemas/config.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Add settings: `COWORK_DB_PATH`, `COWORK_WORKSPACE_ROOT`, `COWORK_MAX_FILE_BYTES`.
- Add application state services: `conversation_service`, `workspace_service`.
- Mount `cowork.router` under `/api/v1`.

- [x] Add the three Cowork configuration fields with conservative local defaults.
- [x] Instantiate services in `create_app()` using the passed settings object.
- [x] Close `conversation_service` during lifespan shutdown.
- [x] Extend CORS methods to include `PUT` because workspace file updates use PUT.
- [x] Mount the Cowork router without modifying existing chat/document route behavior.
- [ ] Run the repository's complete backend tests, lint/security checks, frontend build, and Docker build from a real checkout before merge.
