from __future__ import annotations

import hashlib
from fastapi import APIRouter, HTTPException, Query, Request, status

from app.conversations.service import ConversationNotFound, ConversationService
from app.schemas.cowork import (
    ConversationCreate,
    ConversationView,
    TimelineEventView,
    WorkspaceDirectoryCreate,
    WorkspaceWrite,
)
from app.services.access_control import require_access
from app.workspace.manager import WorkspaceFileTooLarge, WorkspacePathError, WorkspaceService

router = APIRouter()


def _principal_id(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    material = authorization if authorization else "local-access"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _services(request: Request) -> tuple[ConversationService, WorkspaceService]:
    return request.app.state.conversation_service, request.app.state.workspace_service


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")


def _validate_conversation(
    service: ConversationService, principal: str, conversation_id: str
) -> None:
    try:
        service.get(principal, conversation_id)
    except ConversationNotFound as exc:
        raise _not_found() from exc


def _workspace_error(exc: Exception) -> HTTPException:
    if isinstance(exc, WorkspaceFileTooLarge):
        return HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    if isinstance(exc, (WorkspacePathError, UnicodeDecodeError, IsADirectoryError, NotADirectoryError)):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace path not found")
    raise exc


@router.post("/conversations", response_model=ConversationView, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, request: Request) -> ConversationView:
    require_access(request)
    principal = _principal_id(request)
    conversations, workspaces = _services(request)
    conversation = conversations.create(principal, payload.title)
    workspaces.workspace_root(principal, conversation.id)
    conversations.append_event(
        principal,
        conversation.id,
        "conversation.created",
        {"title": conversation.title},
    )
    return ConversationView(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationView)
def get_conversation(conversation_id: str, request: Request) -> ConversationView:
    require_access(request)
    principal = _principal_id(request)
    conversations, _ = _services(request)
    try:
        conversation = conversations.get(principal, conversation_id)
    except ConversationNotFound as exc:
        raise _not_found() from exc
    return ConversationView(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
    )


@router.get(
    "/conversations/{conversation_id}/timeline",
    response_model=list[TimelineEventView],
)
def get_timeline(conversation_id: str, request: Request) -> list[TimelineEventView]:
    require_access(request)
    principal = _principal_id(request)
    conversations, _ = _services(request)
    try:
        events = conversations.timeline(principal, conversation_id)
    except ConversationNotFound as exc:
        raise _not_found() from exc
    return [
        TimelineEventView(
            id=event.id,
            conversation_id=event.conversation_id,
            event_type=event.event_type,
            payload=event.payload,
            created_at=event.created_at,
        )
        for event in events
    ]


@router.get("/conversations/{conversation_id}/workspace")
def list_workspace(
    conversation_id: str,
    request: Request,
    path: str = Query(default=".", max_length=1024),
) -> dict[str, object]:
    require_access(request)
    principal = _principal_id(request)
    conversations, workspaces = _services(request)
    _validate_conversation(conversations, principal, conversation_id)
    try:
        entries = workspaces.list_entries(principal, conversation_id, path)
    except Exception as exc:
        raise _workspace_error(exc) from exc
    return {"path": path, "entries": entries}


@router.post(
    "/conversations/{conversation_id}/workspace/directory",
    status_code=status.HTTP_204_NO_CONTENT,
)
def create_workspace_directory(
    conversation_id: str,
    payload: WorkspaceDirectoryCreate,
    request: Request,
) -> None:
    require_access(request)
    principal = _principal_id(request)
    conversations, workspaces = _services(request)
    _validate_conversation(conversations, principal, conversation_id)
    try:
        workspaces.mkdir(principal, conversation_id, payload.path)
    except Exception as exc:
        raise _workspace_error(exc) from exc
    conversations.append_event(
        principal,
        conversation_id,
        "workspace.directory.created",
        {"path": payload.path},
    )


@router.put(
    "/conversations/{conversation_id}/workspace/file",
    status_code=status.HTTP_204_NO_CONTENT,
)
def write_workspace_file(
    conversation_id: str,
    payload: WorkspaceWrite,
    request: Request,
) -> None:
    require_access(request)
    principal = _principal_id(request)
    conversations, workspaces = _services(request)
    _validate_conversation(conversations, principal, conversation_id)
    try:
        workspaces.write_text(principal, conversation_id, payload.path, payload.content)
    except Exception as exc:
        raise _workspace_error(exc) from exc
    conversations.append_event(
        principal,
        conversation_id,
        "workspace.file.written",
        {"path": payload.path},
    )


@router.get("/conversations/{conversation_id}/workspace/file")
def read_workspace_file(
    conversation_id: str,
    request: Request,
    path: str = Query(min_length=1, max_length=1024),
) -> dict[str, str]:
    require_access(request)
    principal = _principal_id(request)
    conversations, workspaces = _services(request)
    _validate_conversation(conversations, principal, conversation_id)
    try:
        content = workspaces.read_text(principal, conversation_id, path)
    except Exception as exc:
        raise _workspace_error(exc) from exc
    conversations.append_event(
        principal,
        conversation_id,
        "workspace.file.read",
        {"path": path},
    )
    return {"path": path, "content": content}
