"""Audit log model for tracking all user actions."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class AuditLog(Base):
    """
    Comprehensive audit log for tracking all user actions.
    Captures WHO did WHAT, WHEN, and WHERE.
    """
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Who performed the action
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True  # Nullable for system actions
    )
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # What was done
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Where (HTTP details)
    endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status_code: Mapped[Optional[int]] = mapped_column(nullable=True)
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # When
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user={self.user_email})>"


