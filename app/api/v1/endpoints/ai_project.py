"""AI-powered project information generation endpoints."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.ai.project_generator import ProjectInfoGenerator, OperationType
from app.middleware.rbac import require_permission

router = APIRouter()


class ProjectInfoRequest(BaseModel):
    """Request for project information generation."""
    message: str = Field(..., description="User's input/request for project generation")
    operation_type: OperationType = Field(
        default="project_details_generation",
        description="Type of generation: project_title_description_generation, project_details_generation, or project_full_generation"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for generation"
    )


class ProjectInfoResponse(BaseModel):
    """Response from project information generation."""
    success: bool
    response: str = Field(description="Raw AI response")
    parsed_data: Dict[str, Any] = Field(description="Parsed structured data")
    operation_type: str


class TitleDescriptionRequest(BaseModel):
    """Request for title and description generation."""
    idea_or_concept: str = Field(..., description="The idea or concept to generate from")
    context: Optional[Dict[str, Any]] = None


class ProjectDetailsRequest(BaseModel):
    """Request for project details generation."""
    project_title: str = Field(..., description="Project title")
    project_description: Optional[str] = Field(None, description="Optional project description")
    context: Optional[Dict[str, Any]] = None


class FullProjectRequest(BaseModel):
    """Request for full project generation."""
    idea_or_concept: str = Field(..., description="The idea or concept to generate from")
    context: Optional[Dict[str, Any]] = None


@router.post("/generate", response_model=ProjectInfoResponse)
async def generate_project_info(
    request: ProjectInfoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),  # Adjust permission as needed
):
    """
    Generate project information using AI.
    
    This is the main endpoint that mimics your Supabase Edge Function.
    It supports different operation types:
    - project_title_description_generation: Generate title and description
    - project_details_generation: Generate tag, brief, and outcomes
    - project_full_generation: Generate all fields at once
    
    Example:
    ```json
    {
        "message": "Create a mobile app for task management",
        "operation_type": "project_full_generation",
        "context": {
            "industry": "productivity",
            "target_audience": "remote teams"
        }
    }
    ```
    """
    try:
        generator = ProjectInfoGenerator()
        
        result = await generator.generate_project_info(
            message=request.message,
            operation_type=request.operation_type,
            context=request.context,
            user_id=str(current_user.id),
            user_email=current_user.email
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating project information: {str(e)}"
        )


@router.post("/generate-title-description")
async def generate_title_description(
    request: TitleDescriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Generate project title and description from an idea.
    
    Example:
    ```json
    {
        "idea_or_concept": "A platform to connect freelancers with clients",
        "context": {
            "industry": "gig economy"
        }
    }
    ```
    
    Returns:
    ```json
    {
        "title": "Freelancer-Client Matching Platform",
        "description": "A comprehensive platform that connects skilled freelancers..."
    }
    ```
    """
    try:
        generator = ProjectInfoGenerator()
        
        result = await generator.generate_title_description(
            idea_or_concept=request.idea_or_concept,
            context=request.context,
            user_id=str(current_user.id),
            user_email=current_user.email
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating title and description: {str(e)}"
        )


@router.post("/generate-details")
async def generate_project_details(
    request: ProjectDetailsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Generate project details (tag, brief, outcomes) from title and description.
    
    Example:
    ```json
    {
        "project_title": "E-commerce Mobile App",
        "project_description": "A mobile app for online shopping with AI recommendations",
        "context": {
            "platform": "iOS and Android"
        }
    }
    ```
    
    Returns:
    ```json
    {
        "tag": "ECOMMERCE",
        "brief": [
            "User authentication and profiles",
            "Product catalog with search",
            "AI-powered recommendations",
            ...
        ],
        "outcomes": [
            "Increase mobile sales by 30%",
            "Improve user engagement",
            ...
        ]
    }
    ```
    """
    try:
        generator = ProjectInfoGenerator()
        
        result = await generator.generate_project_details(
            project_title=request.project_title,
            project_description=request.project_description,
            context=request.context,
            user_id=str(current_user.id),
            user_email=current_user.email
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating project details: {str(e)}"
        )


@router.post("/generate-full")
async def generate_full_project(
    request: FullProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Generate complete project information from an idea.
    
    This generates everything at once: title, description, tag, brief, and outcomes.
    
    Example:
    ```json
    {
        "idea_or_concept": "AI-powered customer support chatbot",
        "context": {
            "industry": "SaaS",
            "company_size": "startup"
        }
    }
    ```
    
    Returns:
    ```json
    {
        "title": "AI Customer Support Assistant",
        "description": "An intelligent chatbot that provides 24/7 customer support...",
        "tag": "AI",
        "brief": [
            "Natural language processing",
            "Multi-channel support",
            ...
        ],
        "outcomes": [
            "Reduce support costs by 40%",
            "Improve response time",
            ...
        ]
    }
    ```
    """
    try:
        generator = ProjectInfoGenerator()
        
        result = await generator.generate_full_project(
            idea_or_concept=request.idea_or_concept,
            context=request.context,
            user_id=str(current_user.id),
            user_email=current_user.email
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating full project: {str(e)}"
        )
