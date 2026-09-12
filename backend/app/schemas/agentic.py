from pydantic import BaseModel, Field


class AgentView(BaseModel):
    id: str
    name: str
    description: str
    capabilities: list[str]
    allowed_tools: list[str]
    approval_policy: str
    max_runtime_seconds: int
    max_steps: int


class TaskCreate(BaseModel):
    agent_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9_-]+$",
    )
    objective: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = Field(default=None, max_length=128)


class TaskView(BaseModel):
    id: str
    tenant_id: str
    conversation_id: str | None
    agent_id: str
    objective: str
    status: str
    correlation_id: str
    created_at: str
    updated_at: str


class TaskEventView(BaseModel):
    id: str
    task_id: str
    previous_status: str | None
    status: str
    created_at: str
