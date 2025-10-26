"""Audit log API endpoints."""
from typing import Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditLogStatsResponse,
)

router = APIRouter()


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    success: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List audit logs with filtering and pagination.
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if success is not None:
        query = query.filter(AuditLog.success == success)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    # Order by newest first
    query = query.order_by(AuditLog.created_at.desc())
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        logs=logs,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/stats", response_model=AuditLogStatsResponse)
def get_audit_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get audit log statistics.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total actions
    total_actions = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= cutoff_date
    ).scalar()
    
    # Successful actions
    successful_actions = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= cutoff_date,
        AuditLog.success == True
    ).scalar()
    
    # Failed actions
    failed_actions = total_actions - successful_actions
    
    # Unique users
    unique_users = db.query(func.count(distinct(AuditLog.user_id))).filter(
        AuditLog.created_at >= cutoff_date,
        AuditLog.user_id.isnot(None)
    ).scalar()
    
    # Actions by type
    actions_by_type_query = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= cutoff_date
    ).group_by(AuditLog.action).all()
    
    actions_by_type = {action: count for action, count in actions_by_type_query}
    
    # Recent activity (last 24 hours)
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_activity = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= recent_cutoff
    ).scalar()
    
    return AuditLogStatsResponse(
        total_actions=total_actions or 0,
        successful_actions=successful_actions or 0,
        failed_actions=failed_actions or 0,
        unique_users=unique_users or 0,
        actions_by_type=actions_by_type,
        recent_activity=recent_activity or 0,
    )


@router.get("/my-activity", response_model=AuditLogListResponse)
def get_my_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's activity log.
    """
    query = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.created_at.desc())
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        logs=logs,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


