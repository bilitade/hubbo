"""Audit log schemas."""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, UUID4


class AuditLogResponse(BaseModel):
    """Audit log response schema."""
    id: UUID4
    user_id: Optional[UUID4] = None
    user_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: Optional[str] = None
    changes: Optional[dict] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """List of audit logs with pagination."""
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogStatsResponse(BaseModel):
    """Audit log statistics."""
    total_actions: int
    successful_actions: int
    failed_actions: int
    unique_users: int
    actions_by_type: dict[str, int]
    recent_activity: int  # Last 24 hours

