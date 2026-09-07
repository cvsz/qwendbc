from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(0.9, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(2048, ge=1, le=8192)
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[dict]
    usage: dict


class DocumentUpload(BaseModel):
    filename: str
    content: str
    metadata: Optional[dict] = None


class DocumentQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5


class HealthResponse(BaseModel):
    status: str
    version: str
    model_loaded: bool
    timestamp: datetime
    
    class Config:
        protected_namespaces = ()


class ModelInfo(BaseModel):
    name: str
    path: str
    context_length: int
    threads: int
    loaded: bool
