"""User model with role relationships."""
from typing import TYPE_CHECKING, Optional
import uuid
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.token import RefreshToken
    from app.models.password_reset import PasswordResetToken
    from app.models.idea import Idea
    from app.models.knowledge_base import KnowledgeBaseDocument


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """
    Authenticated user with role-based permissions.
    
    Relationships:
        roles: Assigned roles (many-to-many)
        refresh_tokens: Active JWT refresh tokens
    """
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Personal Information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Extended Profile Information (Optional)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Account Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    ideas: Mapped[list["Idea"]] = relationship(
        "Idea",
        foreign_keys="Idea.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    kb_documents: Mapped[list["KnowledgeBaseDocument"]] = relationship(
        "KnowledgeBaseDocument",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Computed Properties
    @property
    def full_name(self) -> str:
        """Returns the full name: first + middle + last"""
        return f"{self.first_name} {self.middle_name} {self.last_name}"
    
    @property
    def preferred_name(self) -> str:
        """Returns display_name if set, otherwise full_name"""
        return self.display_name or self.full_name
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

