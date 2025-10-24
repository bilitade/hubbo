"""Project model with RACI assignments and workflow management."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, ARRAY, Integer, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.idea import Idea
    from app.models.task import Task
    from app.models.experiment import Experiment


class Project(Base):
    """
    Projects generated from Ideas with RACI model and workflow management.
    
    Flow: Created from Ideas → Tasks are assigned → Tracked through workflow steps
    
    Relationships:
        owner: Project owner
        responsible: Responsible person (R in RACI)
        accountable: Accountable person (A in RACI)
        ideas: Source ideas
        tasks: Project tasks
        experiments: Project experiments
    """
    __tablename__ = "projects"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Basic Information
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    project_number: Mapped[Optional[str]] = mapped_column(
        Text,
        unique=True,
        nullable=True
    )
    project_brief: Mapped[str] = mapped_column(Text, nullable=False)
    desired_outcomes: Mapped[str] = mapped_column(Text, nullable=False)
    latest_update: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metrics
    primary_metric: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    secondary_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Status & Workflow
    status: Mapped[str] = mapped_column(
        String(50),
        default="recent",
        nullable=False
    )  # recent, in_progress, completed, on_hold, cancelled
    workflow_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    backlog: Mapped[str] = mapped_column(
        String(50),
        default="business_innovation",
        nullable=False
    )  # business_innovation, product_development, operations
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
    last_activity_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # RACI Model
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
    
    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    responsible: Mapped[Optional["User"]] = relationship("User", foreign_keys=[responsible_id])
    accountable: Mapped[Optional["User"]] = relationship("User", foreign_keys=[accountable_id])
    
    ideas: Mapped[List["Idea"]] = relationship("Idea", back_populates="project")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    experiments: Mapped[List["Experiment"]] = relationship("Experiment", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title='{self.title}', status='{self.status}')>"
