"""User schemas for request/response validation."""
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from app.schemas.role import RoleResponse


class UserBase(BaseModel):
    """Base user schema with common attributes."""
    first_name: str = Field(..., min_length=1, max_length=100, examples=["John"])
    middle_name: str = Field(..., min_length=1, max_length=100, examples=["Michael"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Doe"])
    email: EmailStr = Field(..., examples=["john.doe@example.com"])
    
    # Optional profile fields
    display_name: Optional[str] = Field(None, max_length=255, description="Preferred display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, description="User biography")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    position: Optional[str] = Field(None, max_length=100, description="Job position/title")
    team: Optional[str] = Field(None, max_length=100, description="Team name")
    department: Optional[str] = Field(None, max_length=100, description="Department name")


class UserRegister(UserBase):
    """Public registration schema."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        examples=["SecurePassword123!"]
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


class UserCreate(UserRegister):
    """Admin user creation schema (includes role assignment)."""
    role_names: Optional[List[str]] = Field(
        default=None,
        description="Role names to assign"
    )


class UserProfileUpdate(BaseModel):
    """Self-service profile update schema."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = Field(None, description="Current password (required when changing password)")
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    
    # Optional profile fields
    display_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    team: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


class UserAdminUpdate(BaseModel):
    """Admin user update schema (partial updates)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role_names: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None
    
    # Optional profile fields
    display_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    team: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    is_approved: bool
    roles: List[RoleResponse] = Field(default_factory=list)
    
    # Computed fields (from model properties)
    full_name: Optional[str] = None
    preferred_name: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "first_name": "John",
                "middle_name": "Michael",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "display_name": "Johnny",
                "avatar_url": "https://example.com/avatar.jpg",
                "bio": "Software engineer passionate about clean code",
                "phone": "+1234567890",
                "position": "Senior Software Engineer",
                "team": "Engineering",
                "department": "Product Development",
                "is_active": True,
                "is_approved": True,
                "full_name": "John Michael Doe",
                "preferred_name": "Johnny",
                "roles": [
                    {
                        "id": 1,
                        "name": "admin",
                        "permissions": [
                            {"id": 1, "name": "users:view"}
                        ]
                    }
                ]
            }
        }
    )

