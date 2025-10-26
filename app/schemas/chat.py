"""Chat schemas for request/response validation."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid


# ===== Chat Schemas =====

class ChatBase(BaseModel):
    """Base chat schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ChatCreate(ChatBase):
    """Create chat schema."""
    pass


class ChatUpdate(BaseModel):
    """Update chat schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None


class ChatResponse(ChatBase):
    """Chat response schema."""
    id: uuid.UUID
    user_id: uuid.UUID
    is_archived: bool
    is_pinned: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    thread_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


# ===== Thread Schemas =====

class ChatThreadBase(BaseModel):
    """Base thread schema."""
    title: Optional[str] = Field(None, max_length=200)
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = Field(None, max_length=2000)


class ChatThreadCreate(ChatThreadBase):
    """Create thread schema."""
    chat_id: uuid.UUID


class ChatThreadUpdate(BaseModel):
    """Update thread schema."""
    title: Optional[str] = Field(None, max_length=200)
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None


class ChatThreadResponse(ChatThreadBase):
    """Thread response schema."""
    id: uuid.UUID
    chat_id: uuid.UUID
    is_active: bool
    message_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ===== Message Schemas =====

class ChatMessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, max_length=10000)


class ChatMessageCreate(ChatMessageBase):
    """Create message schema."""
    thread_id: uuid.UUID
    role: str = Field(default="user", pattern="^(user|assistant|system)$")
    extra_data: Optional[Dict[str, Any]] = None


class ChatMessageResponse(ChatMessageBase):
    """Message response schema."""
    id: uuid.UUID
    thread_id: uuid.UUID
    role: str
    extra_data: Optional[Dict[str, Any]]
    model: Optional[str]
    tokens_used: Optional[int]
    user_id: Optional[uuid.UUID]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ===== Assistant Chat Schemas =====

class AssistantChatRequest(BaseModel):
    """Request to chat with AI assistant."""
    thread_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=10000)
    include_project_context: bool = Field(default=False, description="Include project information")
    include_task_context: bool = Field(default=False, description="Include task information")
    project_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "thread_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "What tasks are currently in progress?",
                "include_project_context": True,
                "include_task_context": True
            }
        }
    )


class AssistantChatResponse(BaseModel):
    """Response from AI assistant."""
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    
    model_config = ConfigDict(from_attributes=True)


# ===== Quick Actions =====

class QuickChatRequest(BaseModel):
    """Quick chat without creating explicit thread (auto-creates)."""
    chat_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = Field(None, max_length=2000)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chat_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Tell me about the project status",
                "context": {"project_id": "uuid-here"}
            }
        }
    )


class QuickChatResponse(BaseModel):
    """Quick chat response with thread info."""
    thread: ChatThreadResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


# ===== List Responses =====

class ChatListResponse(BaseModel):
    """List of chats."""
    chats: List[ChatResponse]
    total: int


class ThreadListResponse(BaseModel):
    """List of threads."""
    threads: List[ChatThreadResponse]
    total: int


class MessageListResponse(BaseModel):
    """List of messages."""
    messages: List[ChatMessageResponse]
    total: int


# ===== Context Enhancement =====

class ContextSummaryRequest(BaseModel):
    """Request for context summary."""
    project_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    include_tasks: bool = True
    include_experiments: bool = False
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "include_tasks": True,
                "include_experiments": True
            }
        }
    )


class ContextSummaryResponse(BaseModel):
    """Context summary for AI."""
    summary: str
    context_data: Dict[str, Any]

