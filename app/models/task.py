"""Task model with activities, comments, and attachments."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.idea import Idea
    from app.models.project import Project


class Task(Base):
    """
    Tasks with activities, comments, and attachments.
    
    Relationships:
        idea: Source idea
        project: Parent project
        assigned_to: User assigned to the task
        owner: Task owner
        accountable: Accountable person
        activities: Task activities (checklist items)
        comments: Task comments
        attachments: Task attachments
        activity_logs: Activity history
        responsible_users: Multiple responsible users
    """
    __tablename__ = "tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic Information
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="in_progress",
        nullable=False
    )  # in_progress, completed, blocked, cancelled
    backlog: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
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
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Assignments
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    accountable_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    responsible_role: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accountable_role: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    idea_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ideas.id"),
        nullable=True
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=True
    )
    
    # Relationships
    idea: Mapped[Optional["Idea"]] = relationship("Idea", back_populates="tasks")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="tasks")
    assigned_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to])
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    accountable: Mapped[Optional["User"]] = relationship("User", foreign_keys=[accountable_id])
    
    activities: Mapped[List["TaskActivity"]] = relationship(
        "TaskActivity",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    comments: Mapped[List["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[List["TaskAttachment"]] = relationship(
        "TaskAttachment",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["TaskActivityLog"]] = relationship(
        "TaskActivityLog",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    responsible_users: Mapped[List["TaskResponsibleUser"]] = relationship(
        "TaskResponsibleUser",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class TaskActivity(Base):
    """
    Task activities (checklist items) that can be marked as done/undone.
    """
    __tablename__ = "task_activities"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="activities")
    
    def __repr__(self) -> str:
        return f"<TaskActivity(id={self.id}, title='{self.title}', completed={self.completed})>"


class TaskComment(Base):
    """
    Comments on tasks.
    """
    __tablename__ = "task_comments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="comments")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<TaskComment(id={self.id}, task_id={self.task_id})>"


class TaskAttachment(Base):
    """
    File attachments for tasks.
    """
    __tablename__ = "task_attachments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="attachments")
    uploader: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<TaskAttachment(id={self.id}, file_name='{self.file_name}')>"


class TaskActivityLog(Base):
    """
    Activity log for tracking task changes.
    """
    __tablename__ = "task_activity_log"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="activity_logs")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<TaskActivityLog(id={self.id}, action='{self.action}')>"


class TaskResponsibleUser(Base):
    """
    Multiple responsible users for a task.
    """
    __tablename__ = "task_responsible_users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="responsible_users")
    user: Mapped["User"] = relationship("User")
    
    def __repr__(self) -> str:
        return f"<TaskResponsibleUser(task_id={self.task_id}, user_id={self.user_id})>"
