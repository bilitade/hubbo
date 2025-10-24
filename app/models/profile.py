"""Profile model for extended user information."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Profile(Base):
    """
    Extended user profile information.
    
    Relationships:
        user: Reference to auth.users
        disabled_by_user: User who disabled this profile
    """
    __tablename__ = "profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    
    # Organization info
    team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Security
    needs_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Account status
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    disabled_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    disabled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    disabled_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Relationships
    # user: Mapped["User"] = relationship("User", foreign_keys=[id], back_populates="profile")
    # disabled_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[disabled_by])
    
    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, display_name='{self.display_name}')>"
