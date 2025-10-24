"""AI enhancement endpoints for Ideas, Projects, and Tasks."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from uuid import UUID

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.idea import Idea
from app.models.project import Project
from app.ai.enhancers import IdeaEnhancer, ProjectEnhancer, TaskGenerator
from app.middleware.rbac import require_permission

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class IdeaEnhanceRequest(BaseModel):
    """Request to enhance an idea with AI."""
    title: str = Field(..., description="Current idea title")
    description: Optional[str] = Field(None, description="Current description")
    possible_outcome: Optional[str] = Field(None, description="Current possible outcome")
    departments: Optional[List[str]] = Field(None, description="Departments affected")
    category: Optional[str] = Field(None, description="Idea category")


class IdeaEnhanceResponse(BaseModel):
    """Response from idea enhancement."""
    success: bool
    enhanced_data: Dict[str, Any] = Field(description="Enhanced idea fields")
    raw_response: str = Field(description="Raw AI response")


class ProjectEnhanceRequest(BaseModel):
    """Request to enhance a project with AI."""
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    tag: Optional[str] = Field(None, description="Current tag")
    brief: Optional[str] = Field(None, description="Current brief")
    desired_outcomes: Optional[str] = Field(None, description="Current desired outcomes")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ProjectEnhanceResponse(BaseModel):
    """Response from project enhancement."""
    success: bool
    enhanced_data: Dict[str, Any] = Field(description="Enhanced project fields")
    raw_response: str = Field(description="Raw AI response")


class TaskGenerateRequest(BaseModel):
    """Request to generate tasks for a project."""
    project_title: str = Field(..., description="Project title")
    project_description: Optional[str] = Field(None, description="Project description")
    project_brief: Optional[str] = Field(None, description="Project brief/features")
    project_outcomes: Optional[str] = Field(None, description="Desired outcomes")
    workflow_step: Optional[int] = Field(None, description="Current workflow step")
    num_tasks: int = Field(5, ge=1, le=20, description="Number of tasks to generate")


class TaskGenerateResponse(BaseModel):
    """Response from task generation."""
    success: bool
    tasks: List[Dict[str, Any]] = Field(description="Generated tasks with subtasks")
    raw_response: str = Field(description="Raw AI response")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/enhance-idea", response_model=IdeaEnhanceResponse)
async def enhance_idea(
    request: IdeaEnhanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Enhance an idea with AI-generated improvements.
    
    This endpoint takes the current idea data and returns enhanced versions of:
    - Title (more clear and compelling)
    - Description (more detailed and contextual)
    - Possible Outcome (more specific and measurable)
    
    Example:
    ```json
    {
        "title": "New mobile app",
        "description": "An app for users",
        "possible_outcome": "More users",
        "departments": ["IT", "Marketing"],
        "category": "technology"
    }
    ```
    
    Returns enhanced versions that are more professional and actionable.
    """
    try:
        enhancer = IdeaEnhancer()
        
        result = await enhancer.enhance_idea(
            title=request.title,
            description=request.description,
            possible_outcome=request.possible_outcome,
            departments=request.departments,
            category=request.category
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enhancing idea: {str(e)}"
        )


@router.post("/enhance-idea/{idea_id}", response_model=IdeaEnhanceResponse)
async def enhance_existing_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Enhance an existing idea from the database.
    
    Fetches the idea by ID and enhances it with AI.
    """
    # Get the idea
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Check if user has access
    if idea.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enhance this idea"
        )
    
    try:
        enhancer = IdeaEnhancer()
        
        result = await enhancer.enhance_idea(
            title=idea.title,
            description=idea.description,
            possible_outcome=idea.possible_outcome,
            departments=idea.departments,
            category=idea.category
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enhancing idea: {str(e)}"
        )


@router.post("/enhance-project", response_model=ProjectEnhanceResponse)
async def enhance_project(
    request: ProjectEnhanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Enhance a project with AI-generated details.
    
    This endpoint takes project data and returns enhanced versions with:
    - Improved title and description
    - Professional tag (single UPPERCASE word)
    - Detailed brief (5-8 bullet points of features/deliverables)
    - Specific desired outcomes (3-5 measurable goals)
    
    Example:
    ```json
    {
        "title": "E-commerce Platform",
        "description": "Online store",
        "tag": "SHOP",
        "brief": "Sell products online",
        "desired_outcomes": "Make money",
        "context": {
            "target_market": "B2C",
            "platform": "web and mobile"
        }
    }
    ```
    
    Returns comprehensive project details ready to use.
    """
    try:
        enhancer = ProjectEnhancer()
        
        result = await enhancer.enhance_project(
            title=request.title,
            description=request.description,
            tag=request.tag,
            brief=request.brief,
            desired_outcomes=request.desired_outcomes,
            context=request.context
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enhancing project: {str(e)}"
        )


@router.post("/enhance-project/{project_id}", response_model=ProjectEnhanceResponse)
async def enhance_existing_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Enhance an existing project from the database.
    
    Fetches the project by ID and enhances it with AI.
    """
    # Get the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to enhance this project"
        )
    
    try:
        enhancer = ProjectEnhancer()
        
        result = await enhancer.enhance_project(
            title=project.title,
            description=project.description,
            tag=project.tag,
            brief=project.brief,
            desired_outcomes=project.desired_outcomes
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error enhancing project: {str(e)}"
        )


@router.post("/generate-tasks", response_model=TaskGenerateResponse)
async def generate_tasks(
    request: TaskGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Generate tasks and subtasks for a project using AI.
    
    This endpoint takes project information and generates a comprehensive task breakdown:
    - Main tasks with clear titles and descriptions
    - 3-5 subtasks (activities) for each main task
    - Priority levels (high, medium, low)
    - Logical, sequential task flow
    
    Example:
    ```json
    {
        "project_title": "E-commerce Mobile App",
        "project_description": "Build a mobile app for online shopping",
        "project_brief": "User auth, product catalog, cart, checkout, orders",
        "project_outcomes": "Launch in 3 months, 10k users in first month",
        "workflow_step": 1,
        "num_tasks": 5
    }
    ```
    
    Returns a list of tasks ready to be created in the system.
    Each task includes:
    - title: Task name
    - description: What needs to be done
    - priority: high/medium/low
    - activities: List of subtasks (checklist items)
    """
    try:
        generator = TaskGenerator()
        
        result = await generator.generate_tasks(
            project_title=request.project_title,
            project_description=request.project_description,
            project_brief=request.project_brief,
            project_outcomes=request.project_outcomes,
            workflow_step=request.workflow_step,
            num_tasks=request.num_tasks
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating tasks: {str(e)}"
        )


@router.post("/generate-tasks/{project_id}", response_model=TaskGenerateResponse)
async def generate_tasks_for_project(
    project_id: UUID,
    num_tasks: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Generate tasks for an existing project from the database.
    
    Fetches the project by ID and generates tasks based on its information.
    
    Query Parameters:
    - num_tasks: Number of tasks to generate (default: 5, max: 20)
    """
    # Get the project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate tasks for this project"
        )
    
    try:
        generator = TaskGenerator()
        
        result = await generator.generate_tasks(
            project_title=project.title,
            project_description=project.description,
            project_brief=project.brief,
            project_outcomes=project.desired_outcomes,
            workflow_step=project.workflow_step,
            num_tasks=min(num_tasks, 20)  # Cap at 20
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating tasks: {str(e)}"
        )
