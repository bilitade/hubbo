"""Ideas API endpoints with CRUD operations and RACI model."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from uuid import UUID

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.idea import Idea
from app.models.project import Project
from app.models.task import Task, TaskActivity, TaskActivityLog
from app.schemas.idea import (
    IdeaCreate,
    IdeaUpdate,
    IdeaArchive,
    IdeaMoveToProject,
    IdeaResponse,
    IdeaListResponse,
)
from app.schemas.project import ProjectResponse
from app.middleware.rbac import require_permission

router = APIRouter()


@router.post("/", response_model=IdeaResponse, status_code=status.HTTP_201_CREATED)
def create_idea(
    idea_data: IdeaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),  # Adjust permission as needed
):
    """
    Create a new idea with RACI assignments.
    """
    idea = Idea(
        user_id=current_user.id,
        title=idea_data.title,
        description=idea_data.description,
        possible_outcome=idea_data.possible_outcome,
        category=idea_data.category,
        status=idea_data.status,
        owner_id=idea_data.owner_id,
        responsible_id=idea_data.responsible_id,
        accountable_id=idea_data.accountable_id,
        consulted_ids=idea_data.consulted_ids,
        informed_ids=idea_data.informed_ids,
        departments=idea_data.departments,
    )
    
    db.add(idea)
    db.commit()
    db.refresh(idea)
    
    return idea


@router.get("/", response_model=IdeaListResponse)
def list_ideas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    is_archived: Optional[bool] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    my_items_only: bool = Query(False, description="Filter to only current user's items"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("ideas:view")),
):
    """
    List ideas with filtering and pagination.
    Users with 'ideas:view' permission can see all ideas unless my_items_only=True.
    """
    query = db.query(Idea)
    
    # Optionally filter by user's ideas
    if my_items_only:
        query = query.filter(
            or_(
                Idea.user_id == current_user.id,
                Idea.owner_id == current_user.id,
                Idea.responsible_id == current_user.id,
                Idea.accountable_id == current_user.id,
                Idea.consulted_ids.any(current_user.id),
                Idea.informed_ids.any(current_user.id),
            )
        )
    
    # Apply filters
    if status:
        query = query.filter(Idea.status == status)
    if is_archived is not None:
        query = query.filter(Idea.is_archived == is_archived)
    if category:
        query = query.filter(Idea.category == category)
    if search:
        query = query.filter(
            or_(
                Idea.title.ilike(f"%{search}%"),
                Idea.description.ilike(f"%{search}%"),
            )
        )
    
    total = query.count()
    ideas = query.offset(skip).limit(limit).all()
    
    return IdeaListResponse(
        ideas=ideas,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{idea_id}", response_model=IdeaResponse)
def get_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Get a specific idea by ID.
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Check if user has access to this idea
    if not (
        idea.user_id == current_user.id or
        idea.owner_id == current_user.id or
        idea.responsible_id == current_user.id or
        idea.accountable_id == current_user.id or
        current_user.id in idea.consulted_ids or
        current_user.id in idea.informed_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this idea"
        )
    
    return idea


@router.patch("/{idea_id}", response_model=IdeaResponse)
def update_idea(
    idea_id: UUID,
    idea_data: IdeaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update an idea.
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Check if user has permission to update
    if idea.user_id != current_user.id and idea.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this idea"
        )
    
    # Update fields
    update_data = idea_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(idea, field, value)
    
    db.commit()
    db.refresh(idea)
    
    return idea


@router.delete("/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(
    idea_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete an idea.
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Check if user has permission to delete
    if idea.user_id != current_user.id and idea.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this idea"
        )
    
    db.delete(idea)
    db.commit()
    
    return None


@router.post("/{idea_id}/archive", response_model=IdeaResponse)
def archive_idea(
    idea_id: UUID,
    archive_data: IdeaArchive,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Archive or unarchive an idea.
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Check if user has permission
    if idea.user_id != current_user.id and idea.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to archive this idea"
        )
    
    idea.is_archived = archive_data.is_archived
    db.commit()
    db.refresh(idea)
    
    return idea


@router.post("/{idea_id}/move-to-project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def move_idea_to_project(
    idea_id: UUID,
    project_data: IdeaMoveToProject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Move an idea to a project. Creates a new project based on the idea.
    Optionally generates tasks using AI.
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idea not found"
        )
    
    # Check if user has permission
    if idea.user_id != current_user.id and idea.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to move this idea to project"
        )
    
    # Check if idea is already associated with a project
    if idea.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idea is already associated with a project"
        )
    
    # Create project from idea
    project = Project(
        title=project_data.project_title or idea.title,
        description=idea.description,
        project_brief=project_data.project_brief,
        desired_outcomes=project_data.desired_outcomes,
        owner_id=idea.owner_id or current_user.id,
        responsible_id=idea.responsible_id,
        accountable_id=idea.accountable_id,
        consulted_ids=idea.consulted_ids,
        informed_ids=idea.informed_ids,
        departments=idea.departments,
        due_date=project_data.due_date,
        status="recent",
        workflow_step=1,
    )
    
    db.add(project)
    db.flush()  # Get project ID
    
    # Link idea to project
    idea.project_id = project.id
    idea.status = "in_progress"
    
    # Generate tasks if requested (AI integration point)
    if project_data.generate_tasks_with_ai:
        # TODO: Integrate with AI service to generate tasks
        # For now, create a placeholder task
        task = Task(
            project_id=project.id,
            idea_id=idea.id,
            title=f"Initial task for {project.title}",
            description="This task was auto-generated. Please update with specific details.",
            status="in_progress",
            owner_id=current_user.id,
            assigned_to=idea.responsible_id,
        )
        db.add(task)
        
        # Log the activity
        log = TaskActivityLog(
            task_id=task.id,
            user_id=current_user.id,
            action="created",
            details="Task auto-generated from idea",
        )
        db.add(log)
    
    db.commit()
    db.refresh(project)
    
    return project
