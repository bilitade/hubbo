"""Project schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4


class ProjectBase(BaseModel):
    """Base project schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    project_brief: str = Field(..., min_length=1)
    desired_outcomes: str = Field(..., min_length=1)
    status: str = Field(default="recent")
    backlog: str = Field(default="business_innovation")
    departments: List[str] = Field(default_factory=list)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    owner_id: Optional[UUID4] = None
    responsible_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    consulted_ids: List[UUID4] = Field(default_factory=list)
    informed_ids: List[UUID4] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    workflow_step: int = Field(default=1, ge=1)


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    project_brief: Optional[str] = Field(None, min_length=1)
    desired_outcomes: Optional[str] = Field(None, min_length=1)
    latest_update: Optional[str] = None
    primary_metric: Optional[float] = None
    secondary_metrics: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    backlog: Optional[str] = None
    workflow_step: Optional[int] = Field(None, ge=1)
    owner_id: Optional[UUID4] = None
    responsible_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    consulted_ids: Optional[List[UUID4]] = None
    informed_ids: Optional[List[UUID4]] = None
    due_date: Optional[datetime] = None
    departments: Optional[List[str]] = None
    is_archived: Optional[bool] = None


class ProjectArchive(BaseModel):
    """Schema for archiving a project."""
    is_archived: bool


class ProjectWorkflowUpdate(BaseModel):
    """Schema for updating project workflow step."""
    workflow_step: int = Field(..., ge=1)


class ProjectMetricsUpdate(BaseModel):
    """Schema for updating project metrics."""
    primary_metric: Optional[float] = None
    secondary_metrics: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: UUID4
    project_number: Optional[str] = None
    latest_update: Optional[str] = None
    primary_metric: Optional[float] = None
    secondary_metrics: Optional[Dict[str, Any]] = None
    workflow_step: int
    last_activity_date: datetime
    due_date: Optional[datetime] = None
    owner_id: Optional[UUID4] = None
    responsible_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    consulted_ids: List[UUID4]
    informed_ids: List[UUID4]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Schema for list of projects."""
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int


class ProjectWithTasksResponse(ProjectResponse):
    """Schema for project with tasks."""
    tasks_count: int
    completed_tasks_count: int
    progress_percentage: float
