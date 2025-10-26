"""Chat endpoints - AI assistant chat management."""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid

from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatThreadCreate,
    ChatThreadUpdate,
    ChatThreadResponse,
    ChatMessageResponse,
    AssistantChatRequest,
    AssistantChatResponse,
    QuickChatRequest,
    QuickChatResponse,
    ChatListResponse,
    ThreadListResponse,
    MessageListResponse,
)
from app.ai.chat_service_sync import ChatService
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.chat import Chat, ChatThread, ChatMessage
from app.db.session import get_db
from app.config import settings
from app.middleware.input_sanitizer import InputSanitizer

router = APIRouter()


def check_ai_configured() -> None:
    """Check if AI is properly configured."""
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )


# ===== Chat Management =====

@router.post("/chats", response_model=ChatResponse)
def create_chat(
    request: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new chat."""
    check_ai_configured()
    
    # Sanitize inputs
    title = InputSanitizer.sanitize_text(request.title, max_length=200, field_name="title")
    description = None
    if request.description:
        description = InputSanitizer.sanitize_text(request.description, max_length=1000, field_name="description")
    
    chat_service = ChatService()
    chat = chat_service.create_chat(
        db=db,
        user_id=current_user.id,
        title=title,
        description=description
    )
    
    # Get thread count
    thread_count = db.query(func.count(ChatThread.id)).filter(ChatThread.chat_id == chat.id).scalar() or 0
    
    response = ChatResponse.model_validate(chat)
    response.thread_count = thread_count
    return response


@router.get("/chats", response_model=ChatListResponse)
def list_chats(
    include_archived: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all chats for current user."""
    chat_service = ChatService()
    chats = chat_service.get_user_chats(
        db=db,
        user_id=current_user.id,
        include_archived=include_archived,
        limit=limit
    )
    
    # Add thread counts
    chat_responses = []
    for chat in chats:
        thread_count = db.query(func.count(ChatThread.id)).filter(ChatThread.chat_id == chat.id).scalar() or 0
        
        response = ChatResponse.model_validate(chat)
        response.thread_count = thread_count
        chat_responses.append(response)
    
    return {"chats": chat_responses, "total": len(chat_responses)}


@router.get("/chats/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get thread count
    thread_count = db.query(func.count(ChatThread.id)).filter(ChatThread.chat_id == chat.id).scalar() or 0
    
    response = ChatResponse.model_validate(chat)
    response.thread_count = thread_count
    return response


@router.patch("/chats/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: uuid.UUID,
    request: ChatUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Update fields
    if request.title is not None:
        chat.title = InputSanitizer.sanitize_text(request.title, max_length=200, field_name="title")
    if request.description is not None:
        chat.description = InputSanitizer.sanitize_text(request.description, max_length=1000, field_name="description")
    if request.is_archived is not None:
        chat.is_archived = request.is_archived
    if request.is_pinned is not None:
        chat.is_pinned = request.is_pinned
    
    db.commit()
    db.refresh(chat)
    
    # Get thread count
    thread_count = db.query(func.count(ChatThread.id)).filter(ChatThread.chat_id == chat.id).scalar() or 0
    
    response = ChatResponse.model_validate(chat)
    response.thread_count = thread_count
    return response


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete a chat."""
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()


# ===== Thread Management =====

@router.post("/threads", response_model=ChatThreadResponse)
def create_thread(
    request: ChatThreadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create a new chat thread."""
    check_ai_configured()
    
    # Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == request.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Sanitize inputs
    title = None
    if request.title:
        title = InputSanitizer.sanitize_text(request.title, max_length=200, field_name="title")
    
    system_prompt = None
    if request.system_prompt:
        system_prompt = InputSanitizer.sanitize_ai_prompt(request.system_prompt, "system_prompt")
    
    context = None
    if request.context:
        context = InputSanitizer.sanitize_dict(request.context)
    
    chat_service = ChatService()
    thread = chat_service.create_thread(
        db=db,
        chat_id=request.chat_id,
        title=title,
        context=context,
        system_prompt=system_prompt
    )
    
    return ChatThreadResponse.model_validate(thread)


@router.get("/chats/{chat_id}/threads", response_model=ThreadListResponse)
def list_threads(
    chat_id: uuid.UUID,
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all threads for a chat."""
    # Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat_service = ChatService()
    threads = chat_service.get_chat_threads(
        db=db,
        chat_id=chat_id,
        include_inactive=include_inactive
    )
    
    thread_responses = [ChatThreadResponse.model_validate(t) for t in threads]
    return {"threads": thread_responses, "total": len(thread_responses)}


@router.get("/threads/{thread_id}", response_model=ChatThreadResponse)
def get_thread(
    thread_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get a specific thread."""
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Verify ownership through chat
    chat = db.query(Chat).filter(Chat.id == thread.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return ChatThreadResponse.model_validate(thread)


@router.patch("/threads/{thread_id}", response_model=ChatThreadResponse)
def update_thread(
    thread_id: uuid.UUID,
    request: ChatThreadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update a thread."""
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Verify ownership
    chat = db.query(Chat).filter(Chat.id == thread.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Update fields
    if request.title is not None:
        thread.title = InputSanitizer.sanitize_text(request.title, max_length=200, field_name="title")
    if request.context is not None:
        thread.context = InputSanitizer.sanitize_dict(request.context)
    if request.system_prompt is not None:
        thread.system_prompt = InputSanitizer.sanitize_ai_prompt(request.system_prompt, "system_prompt")
    if request.is_active is not None:
        thread.is_active = request.is_active
    
    db.commit()
    db.refresh(thread)
    
    return ChatThreadResponse.model_validate(thread)


# ===== Messages =====

@router.get("/threads/{thread_id}/messages", response_model=MessageListResponse)
def list_messages(
    thread_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get all messages in a thread."""
    # Verify thread exists and user has access
    thread = db.query(ChatThread).filter(ChatThread.id == thread_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    chat = db.query(Chat).filter(Chat.id == thread.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    chat_service = ChatService()
    messages = chat_service.get_thread_messages(db=db, thread_id=thread_id, limit=limit)
    
    message_responses = [ChatMessageResponse.model_validate(m) for m in messages]
    return {"messages": message_responses, "total": len(message_responses)}


# ===== Assistant Chat =====

@router.post("/assistant/chat", response_model=AssistantChatResponse)
def assistant_chat(
    request: AssistantChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Chat with AI assistant in a thread."""
    check_ai_configured()
    
    # Verify thread exists and user has access
    thread = db.query(ChatThread).filter(ChatThread.id == request.thread_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    chat = db.query(Chat).filter(Chat.id == thread.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Sanitize message
    message = InputSanitizer.sanitize_ai_prompt(request.message, "message")
    
    # Chat with assistant
    chat_service = ChatService()
    user_msg, assistant_msg = chat_service.chat_completion(
        db=db,
        thread_id=request.thread_id,
        user_message=message,
        user_id=current_user.id,
        user=current_user,
        model_name=settings.AI_MODEL,
        include_project_context=request.include_project_context,
        include_task_context=request.include_task_context,
        project_id=request.project_id,
        task_id=request.task_id
    )
    
    return {
        "user_message": ChatMessageResponse.model_validate(user_msg),
        "assistant_message": ChatMessageResponse.model_validate(assistant_msg)
    }


@router.post("/assistant/quick-chat", response_model=QuickChatResponse)
def quick_chat(
    request: QuickChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Quick chat - auto-creates thread and sends message."""
    check_ai_configured()
    
    # Verify chat ownership
    chat = db.query(Chat).filter(Chat.id == request.chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Sanitize inputs
    message = InputSanitizer.sanitize_ai_prompt(request.message, "message")
    context = InputSanitizer.sanitize_dict(request.context) if request.context else None
    system_prompt = None
    if request.system_prompt:
        system_prompt = InputSanitizer.sanitize_ai_prompt(request.system_prompt, "system_prompt")
    
    # Create thread
    chat_service = ChatService()
    thread = chat_service.create_thread(
        db=db,
        chat_id=request.chat_id,
        title=message[:50] + "..." if len(message) > 50 else message,
        context=context,
        system_prompt=system_prompt
    )
    
    # Send message
    user_msg, assistant_msg = chat_service.chat_completion(
        db=db,
        thread_id=thread.id,
        user_message=message,
        user_id=current_user.id,
        user=current_user,
        model_name=settings.AI_MODEL
    )
    
    return {
        "thread": ChatThreadResponse.model_validate(thread),
        "user_message": ChatMessageResponse.model_validate(user_msg),
        "assistant_message": ChatMessageResponse.model_validate(assistant_msg)
    }
