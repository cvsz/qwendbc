from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=200)


class ConversationView(BaseModel):
    id: str
    title: str
    created_at: str


class TimelineEventView(BaseModel):
    id: str
    conversation_id: str
    event_type: str
    payload: dict[str, object]
    created_at: str


class WorkspaceWrite(BaseModel):
    path: str = Field(min_length=1, max_length=1024)
    content: str


class WorkspaceDirectoryCreate(BaseModel):
    path: str = Field(min_length=1, max_length=1024)
