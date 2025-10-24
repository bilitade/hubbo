"""Experiment model for project experiments."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class Experiment(Base):
    """
    Experiments associated with projects.
    
    Relationships:
        project: Parent project
    """
    __tablename__ = "experiments"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Experiment Details
    title: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(Text, nullable=False)
    success_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    progress_updates: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        default=list,
        nullable=True
    )
    
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
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="experiments")
    
    def __repr__(self) -> str:
        return f"<Experiment(id={self.id}, title='{self.title}')>"
