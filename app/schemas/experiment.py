"""Experiment schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4


class ExperimentBase(BaseModel):
    """Base experiment schema."""
    title: str = Field(..., min_length=1, max_length=500)
    hypothesis: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    success_criteria: str = Field(..., min_length=1)


class ExperimentCreate(ExperimentBase):
    """Schema for creating an experiment."""
    project_id: Optional[UUID4] = None
    progress_updates: List[str] = Field(default_factory=list)


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    hypothesis: Optional[str] = Field(None, min_length=1)
    method: Optional[str] = Field(None, min_length=1)
    success_criteria: Optional[str] = Field(None, min_length=1)
    progress_updates: Optional[List[str]] = None


class ExperimentAddUpdate(BaseModel):
    """Schema for adding a progress update to an experiment."""
    update: str = Field(..., min_length=1)


class ExperimentResponse(ExperimentBase):
    """Schema for experiment response."""
    id: UUID4
    project_id: Optional[UUID4] = None
    progress_updates: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ExperimentListResponse(BaseModel):
    """Schema for list of experiments."""
    experiments: List[ExperimentResponse]
    total: int
    page: int
    page_size: int
