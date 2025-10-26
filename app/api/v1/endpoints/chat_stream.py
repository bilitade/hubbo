"""Streaming chat endpoints with SSE (Server-Sent Events)."""
from typing import AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, UUID4
import uuid
import json

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.chat import Chat, ChatThread
from app.ai.chat_service_async_stream import AsyncStreamingChatService
from app.config import settings

router = APIRouter()


class StreamChatRequest(BaseModel):
    """Request for streaming chat."""
    thread_id: UUID4
    message: str
    use_agent: bool = True  # Use agent with tools or simple LLM


def check_ai_configured() -> None:
    """Check if AI is properly configured."""
    if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY."
        )


@router.post("/stream")
async def stream_chat(
    request: StreamChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response with Server-Sent Events (SSE).
    
    Returns a stream of JSON objects:
    - {"type": "user_message", "message_id": "...", "content": "..."}
    - {"type": "content", "chunk": "word"}
    - {"type": "done", "message_id": "...", "total_length": 123}
    - {"type": "error", "message": "..."}
    """
    check_ai_configured()
    
    # Verify thread exists and user has access
    thread = db.query(ChatThread).filter(ChatThread.id == request.thread_id).first()
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    chat = db.query(Chat).filter(
        Chat.id == thread.chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Create streaming service
    chat_service = AsyncStreamingChatService()
    
    async def generate_stream() -> AsyncIterator[str]:
        """Generate SSE stream."""
        try:
            if request.use_agent:
                # Stream with agent (tools + RAG)
                async for chunk in chat_service.stream_agent_response(
                    db=db,
                    thread_id=request.thread_id,
                    user_message=request.message,
                    user=current_user,
                    model_name=settings.AI_MODEL
                ):
                    # chunk is already JSON formatted from service
                    yield f"data: {chunk}\n\n"
            else:
                # Stream simple LLM response
                async for chunk in chat_service.stream_simple_chat(
                    db=db,
                    thread_id=request.thread_id,
                    user_message=request.message,
                    user_id=current_user.id,
                    model_name=settings.AI_MODEL
                ):
                    yield f"data: {chunk}\n\n"
        except Exception as e:
            print(f"❌ Stream error: {e}")
            import traceback
            traceback.print_exc()
            error_data = json.dumps({"type": "error", "message": str(e)})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.post("/quick-stream")
async def quick_stream_chat(
    message: str,
    chat_id: UUID4,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quick streaming chat (creates thread automatically).
    
    Useful for one-off questions without managing threads.
    """
    check_ai_configured()
    
    # Verify chat exists
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Create or get quick thread
    chat_service = AsyncStreamingChatService()
    thread = chat_service.create_thread(
        db=db,
        chat_id=chat_id,
        title="Quick Chat"
    )
    
    async def generate_stream() -> AsyncIterator[str]:
        """Generate SSE stream."""
        async for chunk in chat_service.stream_agent_response(
            db=db,
            thread_id=thread.id,
            user_message=message,
            user=current_user,
            model_name=settings.AI_MODEL
        ):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

