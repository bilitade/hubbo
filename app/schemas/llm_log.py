"""LLM log schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, UUID4


class LLMLogResponse(BaseModel):
    """LLM log response schema."""
    id: UUID4
    user_id: Optional[UUID4] = None
    provider: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    estimated_cost: Optional[float] = None
    endpoint: Optional[str] = None
    feature: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LLMLogListResponse(BaseModel):
    """List of LLM logs with pagination."""
    logs: list[LLMLogResponse]
    total: int
    page: int
    page_size: int


class LLMStatsResponse(BaseModel):
    """LLM usage statistics."""
    # Overall stats
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    
    # Token stats
    total_tokens_used: int
    total_prompt_tokens: int
    total_completion_tokens: int
    average_tokens_per_request: float
    
    # Cost stats
    total_estimated_cost: float
    average_cost_per_request: float
    
    # Performance
    average_latency_ms: float
    
    # Breakdown
    requests_by_model: dict[str, int]
    requests_by_provider: dict[str, int]
    tokens_by_model: dict[str, int]
    
    # Time-based
    requests_today: int
    tokens_today: int

