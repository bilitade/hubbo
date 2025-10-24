"""Idea model with RACI assignments."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.project import Project
    from app.models.task import Task


class Idea(Base):
    """
    Ideas with RACI model for responsibility assignment.
    
    Flow: Ideas can be saved, archived, or moved to Projects.
    
    Relationships:
        user: Creator of the idea
        owner: Owner of the idea
        responsible: Responsible person (R in RACI)
        accountable: Accountable person (A in RACI)
        project: Associated project (when moved to project)
        tasks: Tasks generated from this idea
    """
    __tablename__ = "ideas"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic Information
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    possible_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idea_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="inbox",
        nullable=False
    )  # inbox, in_progress, completed, rejected
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    
    # RACI Model
    owner: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    responsible_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    accountable_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    consulted_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False
    )
    informed_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        nullable=False
    )
    
    # Organization
    departments: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        default=list,
        nullable=False
    )
    
    # Project Association
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="ideas")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="ideas")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="idea", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Idea(id={self.id}, title='{self.title}', status='{self.status}')>"
