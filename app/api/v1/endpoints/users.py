"""User management endpoints."""
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.user import (
    UserRegister,
    UserCreate,
    UserResponse,
    UserProfileUpdate,
    UserAdminUpdate,
)
from app.core.security import hash_password
from app.core.dependencies import get_current_user
from app.middleware import require_permission

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)) -> Any:
    """Public user registration (no authentication required)."""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    new_user = User(
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password=hash_password(user_data.password),
        is_active=True,
        is_approved=False,  # Admin approval required
        # Optional profile fields
        display_name=user_data.display_name,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio,
        phone=user_data.phone,
        position=user_data.position,
        team=user_data.team,
        department=user_data.department
    )
    
    # Assign default "user" role if it exists
    default_role = db.query(Role).filter(Role.name == "normal").first()
    if default_role:
        new_user.roles.append(default_role)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("users:create"))
) -> Any:
    """Admin: Create user with roles (requires 'create_user' permission)."""
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    new_user = User(
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        email=user_data.email,
        password=hash_password(user_data.password),
        is_active=True,
        is_approved=True,
        # Optional profile fields
        display_name=user_data.display_name,
        avatar_url=user_data.avatar_url,
        bio=user_data.bio,
        phone=user_data.phone,
        position=user_data.position,
        team=user_data.team,
        department=user_data.department
    )
    
    if user_data.role_names:
        roles = db.query(Role).filter(Role.name.in_(user_data.role_names)).all()
        new_user.roles = roles
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    user_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update current user profile (self-service)."""
    if user_data.first_name is not None:
        current_user.first_name = user_data.first_name
    
    if user_data.middle_name is not None:
        current_user.middle_name = user_data.middle_name
    
    if user_data.last_name is not None:
        current_user.last_name = user_data.last_name
    
    # Update profile fields
    if user_data.display_name is not None:
        current_user.display_name = user_data.display_name
    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url
    if user_data.bio is not None:
        current_user.bio = user_data.bio
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    if user_data.position is not None:
        current_user.position = user_data.position
    if user_data.team is not None:
        current_user.team = user_data.team
    if user_data.department is not None:
        current_user.department = user_data.department
    
    if user_data.email is not None:
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        current_user.email = user_data.email
    
    if user_data.password is not None:
        # Verify current password before changing
        if not hasattr(user_data, 'current_password') or not user_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required to change password"
            )
        
        from app.core.security import verify_password
        if not verify_password(user_data.current_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        current_user.password = hash_password(user_data.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("users:view"))
) -> Any:
    """Get user by ID (requires 'view_user' permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("users:view"))
) -> Any:
    """List users with pagination (requires 'view_user' permission)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_data: UserAdminUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("users:edit"))
) -> Any:
    """Admin: Update user (partial, requires 'edit_user' permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.first_name is not None:
        user.first_name = user_data.first_name
    
    if user_data.middle_name is not None:
        user.middle_name = user_data.middle_name
    
    if user_data.last_name is not None:
        user.last_name = user_data.last_name
    
    # Update profile fields
    if user_data.display_name is not None:
        user.display_name = user_data.display_name
    if user_data.avatar_url is not None:
        user.avatar_url = user_data.avatar_url
    if user_data.bio is not None:
        user.bio = user_data.bio
    if user_data.phone is not None:
        user.phone = user_data.phone
    if user_data.position is not None:
        user.position = user_data.position
    if user_data.team is not None:
        user.team = user_data.team
    if user_data.department is not None:
        user.department = user_data.department
    
    if user_data.email is not None:
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = user_data.email
    
    if user_data.password is not None:
        user.password = hash_password(user_data.password)
    
    if user_data.role_names is not None:
        roles = db.query(Role).filter(Role.name.in_(user_data.role_names)).all()
        user.roles = roles
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.is_approved is not None:
        user.is_approved = user_data.is_approved
    
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/approve", response_model=UserResponse)
def approve_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("users:approve"))
) -> Any:
    """Admin: Approve user (requires 'users:approve' permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_approved = True
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: bool = Depends(require_permission("users:delete"))
) -> None:
    """Delete user (requires 'delete_user' permission)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()

