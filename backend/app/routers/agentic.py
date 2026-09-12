from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.agentic.domain import InvalidTaskTransition, TaskRecord, TaskStatus
from app.agentic.registry import AgentNotFound, AgentRegistry
from app.agentic.task_store import TaskNotFound, TaskStore
from app.schemas.agentic import AgentView, TaskCreate, TaskEventView, TaskView
from app.services.access_control import require_access

router = APIRouter()


def _services(request: Request) -> tuple[AgentRegistry, TaskStore]:
    return request.app.state.agent_registry, request.app.state.task_store


def _task_view(task: TaskRecord) -> TaskView:
    return TaskView(
        id=task.id,
        tenant_id=task.tenant_id,
        conversation_id=task.conversation_id,
        agent_id=task.agent_id,
        objective=task.objective,
        status=task.status.value,
        correlation_id=task.correlation_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/agents", response_model=list[AgentView])
def list_agents(request: Request) -> list[AgentView]:
    require_access(request)
    registry, _ = _services(request)
    return [
        AgentView(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            capabilities=list(agent.capabilities),
            allowed_tools=list(agent.allowed_tools),
            approval_policy=agent.approval_policy,
            max_runtime_seconds=agent.max_runtime_seconds,
            max_steps=agent.max_steps,
        )
        for agent in registry.list()
    ]


@router.post(
    "/tasks",
    response_model=TaskView,
    status_code=status.HTTP_201_CREATED,
)
def create_task(payload: TaskCreate, request: Request) -> TaskView:
    context = require_access(request)
    registry, store = _services(request)
    try:
        registry.get(payload.agent_id)
    except AgentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unknown agent",
        ) from exc
    task = store.create(
        tenant_id=context.tenant_id,
        principal_id=context.principal_id,
        conversation_id=payload.conversation_id,
        agent_id=payload.agent_id,
        objective=payload.objective,
    )
    return _task_view(task)


@router.get("/tasks", response_model=list[TaskView])
def list_tasks(request: Request) -> list[TaskView]:
    context = require_access(request)
    _, store = _services(request)
    return [
        _task_view(task)
        for task in store.list(context.tenant_id, context.principal_id)
    ]


@router.get("/tasks/{task_id}", response_model=TaskView)
def get_task(task_id: str, request: Request) -> TaskView:
    context = require_access(request)
    _, store = _services(request)
    try:
        task = store.get(context.tenant_id, context.principal_id, task_id)
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    return _task_view(task)


@router.post("/tasks/{task_id}/queue", response_model=TaskView)
def queue_task(task_id: str, request: Request) -> TaskView:
    context = require_access(request)
    _, store = _services(request)
    try:
        task = store.transition(
            context.tenant_id,
            context.principal_id,
            task_id,
            TaskStatus.QUEUED,
        )
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    except InvalidTaskTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return _task_view(task)


@router.post("/tasks/{task_id}/cancel", response_model=TaskView)
def cancel_task(task_id: str, request: Request) -> TaskView:
    context = require_access(request)
    _, store = _services(request)
    try:
        task = store.transition(
            context.tenant_id,
            context.principal_id,
            task_id,
            TaskStatus.CANCELLED,
        )
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    except InvalidTaskTransition as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return _task_view(task)


@router.get(
    "/tasks/{task_id}/events",
    response_model=list[TaskEventView],
)
def task_events(task_id: str, request: Request) -> list[TaskEventView]:
    context = require_access(request)
    _, store = _services(request)
    try:
        events = store.events(
            context.tenant_id,
            context.principal_id,
            task_id,
        )
    except TaskNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from exc
    return [
        TaskEventView(
            id=event.id,
            task_id=event.task_id,
            previous_status=(
                event.previous_status.value
                if event.previous_status is not None
                else None
            ),
            status=event.status.value,
            created_at=event.created_at,
        )
        for event in events
    ]
