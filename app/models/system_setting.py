"""System settings model for runtime configuration."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.base import Base


class SystemSetting(Base):
    """
    System-wide settings that can be updated at runtime.
    These override environment variables when set.
    """
    __tablename__ = "system_settings"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # General Settings
    app_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    frontend_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # AI Configuration
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    openai_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    anthropic_api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Email Configuration
    mail_server: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mail_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mail_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mail_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mail_from: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mail_from_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mail_starttls: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    mail_ssl_tls: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Storage Configuration
    max_upload_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    upload_dir: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vector_store_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Feature Flags
    enable_streaming: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    enable_agent: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    enable_knowledge_base: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Metadata
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
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<SystemSetting(id={self.id}, ai_provider='{self.ai_provider}')>"

