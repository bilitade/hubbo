"""Idea schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4


class IdeaBase(BaseModel):
    """Base idea schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    possible_outcome: str = Field(..., min_length=1)
    category: Optional[str] = None
    status: str = Field(default="inbox")
    departments: List[str] = Field(default_factory=list)


class IdeaCreate(IdeaBase):
    """Schema for creating an idea."""
    owner_id: Optional[UUID4] = None
    responsible_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    consulted_ids: List[UUID4] = Field(default_factory=list)
    informed_ids: List[UUID4] = Field(default_factory=list)


class IdeaUpdate(BaseModel):
    """Schema for updating an idea."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    possible_outcome: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[UUID4] = None
    responsible_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    consulted_ids: Optional[List[UUID4]] = None
    informed_ids: Optional[List[UUID4]] = None
    departments: Optional[List[str]] = None
    is_archived: Optional[bool] = None


class IdeaArchive(BaseModel):
    """Schema for archiving an idea."""
    is_archived: bool


class IdeaMoveToProject(BaseModel):
    """Schema for moving an idea to a project."""
    project_title: Optional[str] = Field(None, min_length=1, max_length=500)
    project_brief: str = Field(..., min_length=1)
    desired_outcomes: str = Field(..., min_length=1)
    due_date: Optional[datetime] = None
    generate_tasks_with_ai: bool = Field(default=False)


class IdeaResponse(IdeaBase):
    """Schema for idea response."""
    id: UUID4
    user_id: UUID4
    idea_id: Optional[str] = None
    owner: Optional[UUID4] = None
    owner_id: Optional[UUID4] = None
    responsible_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    consulted_ids: List[UUID4]
    informed_ids: List[UUID4]
    project_id: Optional[UUID4] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IdeaListResponse(BaseModel):
    """Schema for list of ideas."""
    ideas: List[IdeaResponse]
    total: int
    page: int
    page_size: int
