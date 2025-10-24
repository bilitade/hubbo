"""Profile schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, UUID4


class ProfileBase(BaseModel):
    """Base profile schema."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None


class ProfileCreate(ProfileBase):
    """Schema for creating a profile."""
    id: UUID4


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    team: Optional[str] = None
    position: Optional[str] = None
    email: Optional[str] = None
    needs_password_change: Optional[bool] = None


class ProfileDisable(BaseModel):
    """Schema for disabling a profile."""
    disabled_reason: str = Field(..., min_length=1, max_length=500)


class ProfileResponse(ProfileBase):
    """Schema for profile response."""
    id: UUID4
    created_at: datetime
    updated_at: datetime
    needs_password_change: bool
    disabled: bool
    disabled_reason: Optional[str] = None
    disabled_at: Optional[datetime] = None
    disabled_by: Optional[UUID4] = None
    
    class Config:
        from_attributes = True
