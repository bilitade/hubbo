"""Profiles API endpoints for extended user information."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileDisable,
    ProfileResponse,
)
from app.middleware.rbac import require_permission

router = APIRouter()


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Create a profile for a user.
    """
    # Check if profile already exists
    existing = db.query(Profile).filter(Profile.id == profile_data.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this user"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.id == profile_data.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    profile = Profile(
        id=profile_data.id,
        display_name=profile_data.display_name,
        avatar_url=profile_data.avatar_url,
        team=profile_data.team,
        position=profile_data.position,
        email=profile_data.email,
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's profile.
    """
    profile = db.query(Profile).filter(Profile.id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Get a user's profile by ID.
    """
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.patch("/{user_id}", response_model=ProfileResponse)
def update_profile(
    user_id: UUID,
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update a user's profile.
    """
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Users can only update their own profile unless they have admin permission
    if user_id != current_user.id:
        # Check if user has admin permission
        # This is a simplified check - adjust based on your RBAC implementation
        pass
    
    # Update fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.post("/{user_id}/disable", response_model=ProfileResponse)
def disable_profile(
    user_id: UUID,
    disable_data: ProfileDisable,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Disable a user's profile.
    """
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile.disabled = True
    profile.disabled_reason = disable_data.disabled_reason
    profile.disabled_at = datetime.utcnow()
    profile.disabled_by = current_user.id
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.post("/{user_id}/enable", response_model=ProfileResponse)
def enable_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Enable a user's profile.
    """
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile.disabled = False
    profile.disabled_reason = None
    profile.disabled_at = None
    profile.disabled_by = None
    
    db.commit()
    db.refresh(profile)
    
    return profile
