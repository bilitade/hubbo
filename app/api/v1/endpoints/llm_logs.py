"""LLM log API endpoints."""
from typing import Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.llm_log import LLMLog
from app.schemas.llm_log import (
    LLMLogResponse,
    LLMLogListResponse,
    LLMStatsResponse,
)

router = APIRouter()


@router.get("/", response_model=LLMLogListResponse)
def list_llm_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    success: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    List LLM logs with filtering and pagination.
    """
    query = db.query(LLMLog)
    
    # Apply filters
    if user_id:
        query = query.filter(LLMLog.user_id == user_id)
    if provider:
        query = query.filter(LLMLog.provider == provider)
    if model:
        query = query.filter(LLMLog.model == model)
    if success is not None:
        query = query.filter(LLMLog.success == success)
    if start_date:
        query = query.filter(LLMLog.created_at >= start_date)
    if end_date:
        query = query.filter(LLMLog.created_at <= end_date)
    
    # Order by newest first
    query = query.order_by(LLMLog.created_at.desc())
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return LLMLogListResponse(
        logs=logs,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/stats", response_model=LLMStatsResponse)
def get_llm_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get LLM usage statistics.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total requests
    total_requests = db.query(func.count(LLMLog.id)).filter(
        LLMLog.created_at >= cutoff_date
    ).scalar() or 0
    
    # Successful/Failed requests
    successful_requests = db.query(func.count(LLMLog.id)).filter(
        LLMLog.created_at >= cutoff_date,
        LLMLog.success == True
    ).scalar() or 0
    
    failed_requests = total_requests - successful_requests
    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0.0
    
    # Token stats
    token_stats = db.query(
        func.sum(LLMLog.total_tokens).label('total'),
        func.sum(LLMLog.prompt_tokens).label('prompt'),
        func.sum(LLMLog.completion_tokens).label('completion'),
        func.avg(LLMLog.total_tokens).label('average'),
    ).filter(
        LLMLog.created_at >= cutoff_date
    ).first()
    
    total_tokens = int(token_stats.total or 0)
    prompt_tokens = int(token_stats.prompt or 0)
    completion_tokens = int(token_stats.completion or 0)
    avg_tokens = float(token_stats.average or 0)
    
    # Cost stats
    cost_stats = db.query(
        func.sum(LLMLog.estimated_cost).label('total'),
        func.avg(LLMLog.estimated_cost).label('average'),
    ).filter(
        LLMLog.created_at >= cutoff_date
    ).first()
    
    total_cost = float(cost_stats.total or 0)
    avg_cost = float(cost_stats.average or 0)
    
    # Latency stats
    avg_latency = db.query(func.avg(LLMLog.latency_ms)).filter(
        LLMLog.created_at >= cutoff_date,
        LLMLog.latency_ms.isnot(None)
    ).scalar() or 0
    
    # Requests by model
    model_stats = db.query(
        LLMLog.model,
        func.count(LLMLog.id).label('count')
    ).filter(
        LLMLog.created_at >= cutoff_date
    ).group_by(LLMLog.model).all()
    
    requests_by_model = {model: count for model, count in model_stats}
    
    # Requests by provider
    provider_stats = db.query(
        LLMLog.provider,
        func.count(LLMLog.id).label('count')
    ).filter(
        LLMLog.created_at >= cutoff_date
    ).group_by(LLMLog.provider).all()
    
    requests_by_provider = {provider: count for provider, count in provider_stats}
    
    # Tokens by model
    tokens_by_model_stats = db.query(
        LLMLog.model,
        func.sum(LLMLog.total_tokens).label('tokens')
    ).filter(
        LLMLog.created_at >= cutoff_date
    ).group_by(LLMLog.model).all()
    
    tokens_by_model = {model: int(tokens or 0) for model, tokens in tokens_by_model_stats}
    
    # Today's stats
    requests_today = db.query(func.count(LLMLog.id)).filter(
        LLMLog.created_at >= today_start
    ).scalar() or 0
    
    tokens_today = db.query(func.sum(LLMLog.total_tokens)).filter(
        LLMLog.created_at >= today_start
    ).scalar() or 0
    
    return LLMStatsResponse(
        total_requests=total_requests,
        successful_requests=successful_requests,
        failed_requests=failed_requests,
        success_rate=round(success_rate, 2),
        total_tokens_used=total_tokens,
        total_prompt_tokens=prompt_tokens,
        total_completion_tokens=completion_tokens,
        average_tokens_per_request=round(avg_tokens, 2),
        total_estimated_cost=round(total_cost, 4),
        average_cost_per_request=round(avg_cost, 6),
        average_latency_ms=round(float(avg_latency), 2),
        requests_by_model=requests_by_model,
        requests_by_provider=requests_by_provider,
        tokens_by_model=tokens_by_model,
        requests_today=requests_today,
        tokens_today=int(tokens_today or 0),
    )


@router.get("/my-usage", response_model=LLMLogListResponse)
def get_my_llm_usage(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's LLM usage.
    """
    query = db.query(LLMLog).filter(
        LLMLog.user_id == current_user.id
    ).order_by(LLMLog.created_at.desc())
    
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    
    return LLMLogListResponse(
        logs=logs,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


