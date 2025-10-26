"""System settings API endpoints."""
from typing import Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.system_setting import SystemSetting
from app.schemas.system_settings import (
    SystemSettingsUpdate,
    SystemSettingsResponse,
    SystemSettingsPublicResponse,
)
from app.middleware.rbac import require_permission
from app.config import settings as app_settings

router = APIRouter()


def mask_sensitive_value(value: Optional[str]) -> Optional[str]:
    """Mask sensitive values for display."""
    if not value or len(value) < 8:
        return "••••••••"
    return f"{value[:4]}{'•' * (len(value) - 8)}{value[-4:]}"


@router.get("/", response_model=SystemSettingsResponse)
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current system settings.
    Sensitive values are masked.
    """
    # Get from database or create default
    setting = db.query(SystemSetting).first()
    
    if not setting:
        # Return current environment settings
        return SystemSettingsResponse(
            id="00000000-0000-0000-0000-000000000000",
            app_name=app_settings.APP_NAME,
            frontend_url=app_settings.FRONTEND_URL,
            ai_provider=app_settings.AI_PROVIDER,
            ai_model=app_settings.AI_MODEL,
            ai_temperature=app_settings.AI_TEMPERATURE,
            ai_max_tokens=app_settings.AI_MAX_TOKENS,
            embedding_model=app_settings.EMBEDDING_MODEL,
            mail_server=app_settings.MAIL_SERVER,
            mail_port=app_settings.MAIL_PORT,
            mail_username=app_settings.MAIL_USERNAME,
            mail_from=app_settings.MAIL_FROM,
            mail_from_name=app_settings.MAIL_FROM_NAME,
            mail_starttls=app_settings.MAIL_STARTTLS,
            mail_ssl_tls=app_settings.MAIL_SSL_TLS,
            max_upload_size=app_settings.MAX_UPLOAD_SIZE,
            upload_dir=app_settings.UPLOAD_DIR,
            vector_store_path=app_settings.VECTOR_STORE_PATH,
            enable_streaming=True,
            enable_agent=True,
            enable_knowledge_base=True,
            openai_api_key_masked=mask_sensitive_value(app_settings.OPENAI_API_KEY),
            anthropic_api_key_masked=mask_sensitive_value(app_settings.ANTHROPIC_API_KEY),
            mail_password_masked=mask_sensitive_value(app_settings.MAIL_PASSWORD),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    
    # Mask sensitive fields
    response = SystemSettingsResponse.from_orm(setting)
    response.openai_api_key_masked = mask_sensitive_value(setting.openai_api_key)
    response.anthropic_api_key_masked = mask_sensitive_value(setting.anthropic_api_key)
    response.mail_password_masked = mask_sensitive_value(setting.mail_password)
    
    # Don't send actual keys
    response.openai_api_key = None
    response.anthropic_api_key = None
    response.mail_password = None
    
    return response


@router.get("/public", response_model=SystemSettingsPublicResponse)
def get_public_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get public system settings (non-sensitive).
    Available to all authenticated users.
    """
    setting = db.query(SystemSetting).first()
    
    if not setting:
        return SystemSettingsPublicResponse(
            app_name=app_settings.APP_NAME,
            ai_provider=app_settings.AI_PROVIDER,
            ai_model=app_settings.AI_MODEL,
            ai_temperature=app_settings.AI_TEMPERATURE,
            ai_max_tokens=app_settings.AI_MAX_TOKENS,
            max_upload_size=app_settings.MAX_UPLOAD_SIZE,
            enable_streaming=True,
            enable_agent=True,
            enable_knowledge_base=True,
        )
    
    return SystemSettingsPublicResponse.from_orm(setting)


@router.patch("/", response_model=SystemSettingsResponse)
def update_system_settings(
    settings_data: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update system settings.
    Creates settings record if it doesn't exist.
    """
    setting = db.query(SystemSetting).first()
    
    if not setting:
        # Create new settings record
        setting = SystemSetting(
            updated_by=current_user.id
        )
        db.add(setting)
    else:
        setting.updated_by = current_user.id
        setting.updated_at = datetime.utcnow()
    
    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:  # Only update if value is provided
            setattr(setting, field, value)
    
    db.commit()
    db.refresh(setting)
    
    # Prepare response with masked sensitive data
    response = SystemSettingsResponse.from_orm(setting)
    response.openai_api_key_masked = mask_sensitive_value(setting.openai_api_key)
    response.anthropic_api_key_masked = mask_sensitive_value(setting.anthropic_api_key)
    response.mail_password_masked = mask_sensitive_value(setting.mail_password)
    
    # Don't send actual keys
    response.openai_api_key = None
    response.anthropic_api_key = None
    response.mail_password = None
    
    return response


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def reset_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Reset system settings to environment defaults.
    Deletes the settings record.
    """
    setting = db.query(SystemSetting).first()
    
    if setting:
        db.delete(setting)
        db.commit()
    
    return None

