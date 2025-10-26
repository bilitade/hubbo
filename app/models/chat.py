"""Chat models for AI assistant conversations."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Chat(Base):
    """
    Chat container - top level chat organization.
    
    A user can have multiple chats, each containing threads of conversations.
    """
    __tablename__ = "chats"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic Information
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # User
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    threads: Mapped[List["ChatThread"]] = relationship(
        "ChatThread",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ChatThread.created_at.desc()"
    )
    
    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title='{self.title}')>"


class ChatThread(Base):
    """
    Chat thread - a conversation thread within a chat.
    
    Each thread has a context and contains multiple messages.
    """
    __tablename__ = "chat_threads"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Chat reference
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Thread Information
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context - can include project_id, task_id, etc for context-aware responses
    context: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # System prompt for this thread
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Message count for quick reference
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="threads")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()"
    )
    
    def __repr__(self) -> str:
        return f"<ChatThread(id={self.id}, chat_id={self.chat_id})>"


class ChatMessage(Base):
    """
    Individual messages in a chat thread.
    
    Can be user messages or assistant (system) responses.
    """
    __tablename__ = "chat_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Thread reference
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Message Information
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # user, assistant, system
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Extra data/metadata
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Model used (for assistant messages)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Tokens used (for cost tracking)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # User reference (for user messages)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    thread: Mapped["ChatThread"] = relationship("ChatThread", back_populates="messages")
    user: Mapped[Optional["User"]] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role='{self.role}')>"

