"""System settings schemas for configuration management."""
from typing import Optional
from pydantic import BaseModel, Field, UUID4
from datetime import datetime


class SystemSettingsBase(BaseModel):
    """Base system settings schema."""
    # General
    app_name: Optional[str] = None
    frontend_url: Optional[str] = None
    
    # AI Configuration
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    ai_max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    embedding_model: Optional[str] = None
    
    # Email Configuration
    mail_server: Optional[str] = None
    mail_port: Optional[int] = Field(None, ge=1, le=65535)
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_from_name: Optional[str] = None
    mail_starttls: Optional[bool] = None
    mail_ssl_tls: Optional[bool] = None
    
    # Storage Configuration
    max_upload_size: Optional[int] = Field(None, ge=1024, description="Max upload size in bytes")
    upload_dir: Optional[str] = None
    vector_store_path: Optional[str] = None
    
    # Feature Flags
    enable_streaming: Optional[bool] = None
    enable_agent: Optional[bool] = None
    enable_knowledge_base: Optional[bool] = None


class SystemSettingsUpdate(SystemSettingsBase):
    """Schema for updating system settings."""
    pass


class SystemSettingsResponse(SystemSettingsBase):
    """Schema for system settings response."""
    id: UUID4
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[UUID4] = None
    
    # Masked API keys for security
    openai_api_key_masked: Optional[str] = None
    anthropic_api_key_masked: Optional[str] = None
    mail_password_masked: Optional[str] = None
    
    class Config:
        from_attributes = True


class SystemSettingsPublicResponse(BaseModel):
    """Public system settings response (no sensitive data)."""
    app_name: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None
    max_upload_size: Optional[int] = None
    enable_streaming: Optional[bool] = None
    enable_agent: Optional[bool] = None
    enable_knowledge_base: Optional[bool] = None
    
    class Config:
        from_attributes = True

