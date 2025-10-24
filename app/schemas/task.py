"""Task schemas for request/response validation."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4


# Task Activity Schemas
class TaskActivityBase(BaseModel):
    """Base task activity schema."""
    title: str = Field(..., min_length=1, max_length=500)
    completed: bool = Field(default=False)


class TaskActivityCreate(TaskActivityBase):
    """Schema for creating a task activity."""
    pass


class TaskActivityUpdate(BaseModel):
    """Schema for updating a task activity."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    completed: Optional[bool] = None


class TaskActivityResponse(TaskActivityBase):
    """Schema for task activity response."""
    id: UUID4
    task_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Task Comment Schemas
class TaskCommentBase(BaseModel):
    """Base task comment schema."""
    content: str = Field(..., min_length=1)


class TaskCommentCreate(TaskCommentBase):
    """Schema for creating a task comment."""
    pass


class TaskCommentResponse(TaskCommentBase):
    """Schema for task comment response."""
    id: UUID4
    task_id: UUID4
    user_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


# Task Attachment Schemas
class TaskAttachmentResponse(BaseModel):
    """Schema for task attachment response."""
    id: UUID4
    task_id: UUID4
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


# Task Activity Log Schemas
class TaskActivityLogResponse(BaseModel):
    """Schema for task activity log response."""
    id: UUID4
    task_id: UUID4
    user_id: UUID4
    action: str
    details: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Task Responsible User Schemas
class TaskResponsibleUserCreate(BaseModel):
    """Schema for adding a responsible user to a task."""
    user_id: UUID4


class TaskResponsibleUserResponse(BaseModel):
    """Schema for task responsible user response."""
    id: UUID4
    task_id: UUID4
    user_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


# Main Task Schemas
class TaskBase(BaseModel):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status: str = Field(default="in_progress")
    backlog: Optional[str] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    idea_id: Optional[UUID4] = None
    project_id: Optional[UUID4] = None
    assigned_to: Optional[UUID4] = None
    owner_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    responsible_role: Optional[str] = None
    accountable_role: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    activities: List[TaskActivityCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None
    backlog: Optional[str] = None
    assigned_to: Optional[UUID4] = None
    owner_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    responsible_role: Optional[str] = None
    accountable_role: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    """Schema for task response."""
    id: UUID4
    idea_id: Optional[UUID4] = None
    project_id: Optional[UUID4] = None
    assigned_to: Optional[UUID4] = None
    owner_id: Optional[UUID4] = None
    accountable_id: Optional[UUID4] = None
    responsible_role: Optional[str] = None
    accountable_role: Optional[str] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    """Schema for detailed task response with activities, comments, etc."""
    activities: List[TaskActivityResponse] = Field(default_factory=list)
    comments: List[TaskCommentResponse] = Field(default_factory=list)
    attachments: List[TaskAttachmentResponse] = Field(default_factory=list)
    responsible_users: List[TaskResponsibleUserResponse] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    """Schema for list of tasks."""
    tasks: List[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskBulkCreate(BaseModel):
    """Schema for bulk creating tasks."""
    tasks: List[TaskCreate] = Field(..., min_items=1, max_items=50)
