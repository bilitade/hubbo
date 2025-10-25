"""Projects API endpoints with CRUD operations and workflow management."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectArchive,
    ProjectWorkflowUpdate,
    ProjectMetricsUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectWithTasksResponse,
)
from app.middleware.rbac import require_permission
from app.utils.project_progress import calculate_project_progress, auto_update_project_status

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Create a new project with RACI assignments.
    """
    # Generate unique project number by finding the max existing number
    max_project_number = db.query(func.max(Project.project_number)).scalar()
    
    if max_project_number:
        # Extract the number from format PRJ-00001
        try:
            last_number = int(max_project_number.split('-')[1])
            next_number = last_number + 1
        except (IndexError, ValueError):
            # Fallback if format is unexpected
            next_number = db.query(func.count(Project.id)).scalar() + 1
    else:
        next_number = 1
    
    project_number = f"PRJ-{next_number:05d}"
    
    project = Project(
        title=project_data.title,
        description=project_data.description,
        project_brief=project_data.project_brief,
        desired_outcomes=project_data.desired_outcomes,
        project_number=project_number,
        status="planning",  # Always start with planning status
        backlog=project_data.backlog,
        workflow_step=project_data.workflow_step,
        owner_id=project_data.owner_id or current_user.id,
        responsible_id=project_data.responsible_id,
        accountable_id=project_data.accountable_id,
        consulted_ids=project_data.consulted_ids,
        informed_ids=project_data.informed_ids,
        due_date=project_data.due_date,
        departments=project_data.departments,
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    is_archived: Optional[bool] = None,
    backlog: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List projects with filtering, pagination, and task statistics.
    """
    query = db.query(Project)
    
    # Filter by user's projects or projects where user is involved
    query = query.filter(
        or_(
            Project.owner_id == current_user.id,
            Project.responsible_id == current_user.id,
            Project.accountable_id == current_user.id,
            Project.consulted_ids.any(current_user.id),
            Project.informed_ids.any(current_user.id),
        )
    )
    
    # Apply filters
    if status:
        query = query.filter(Project.status == status)
    if is_archived is not None:
        query = query.filter(Project.is_archived == is_archived)
    if backlog:
        query = query.filter(Project.backlog == backlog)
    if search:
        query = query.filter(
            or_(
                Project.title.ilike(f"%{search}%"),
                Project.description.ilike(f"%{search}%"),
                Project.project_number.ilike(f"%{search}%"),
            )
        )
    
    # Order by last activity
    query = query.order_by(Project.last_activity_date.desc())
    
    total = query.count()
    projects = query.offset(skip).limit(limit).all()
    
    # Calculate progress for each project
    enriched_projects = []
    for project in projects:
        # Auto-update status
        new_status = auto_update_project_status(db, project)
        if project.status != new_status:
            project.status = new_status
            db.commit()
            db.refresh(project)
        
        # Calculate progress
        progress_percentage, total_items, completed_items, tasks_count, completed_tasks_count = calculate_project_progress(db, project.id)
        
        # Add statistics to project dict
        project_dict = {
            **project.__dict__,
            "progress_percentage": progress_percentage,
            "tasks_count": tasks_count,
            "completed_tasks_count": completed_tasks_count,
            "unassigned_tasks_count": db.query(func.count(Task.id)).filter(
                Task.project_id == project.id,
                Task.status == "unassigned"
            ).scalar() or 0,
            "in_progress_tasks_count": db.query(func.count(Task.id)).filter(
                Task.project_id == project.id,
                Task.status == "in_progress"
            ).scalar() or 0,
        }
        
        enriched_projects.append(project_dict)
    
    return ProjectListResponse(
        projects=enriched_projects,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{project_id}", response_model=ProjectWithTasksResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Get a specific project by ID with task statistics.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has access to this project
    if not (
        project.owner_id == current_user.id or
        project.responsible_id == current_user.id or
        project.accountable_id == current_user.id or
        current_user.id in project.consulted_ids or
        current_user.id in project.informed_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Auto-update project status based on tasks
    new_status = auto_update_project_status(db, project)
    if project.status != new_status:
        project.status = new_status
        db.commit()
        db.refresh(project)
    
    # Calculate progress including tasks and subtasks
    progress_percentage, total_items, completed_items, tasks_count, completed_tasks_count = calculate_project_progress(db, project_id)
    
    # Convert to response model
    project_dict = {
        **project.__dict__,
        "tasks_count": tasks_count,
        "completed_tasks_count": completed_tasks_count,
        "progress_percentage": progress_percentage,
    }
    
    return ProjectWithTasksResponse(**project_dict)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission to update
    if project.owner_id != current_user.id and project.accountable_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this project"
        )
    
    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    # Update last activity date
    project.last_activity_date = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission to delete
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this project"
        )
    
    db.delete(project)
    db.commit()
    
    return None


@router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(
    project_id: UUID,
    archive_data: ProjectArchive,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Archive or unarchive a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission
    if project.owner_id != current_user.id and project.accountable_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to archive this project"
        )
    
    project.is_archived = archive_data.is_archived
    project.last_activity_date = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return project


@router.patch("/{project_id}/workflow", response_model=ProjectResponse)
def update_project_workflow(
    project_id: UUID,
    workflow_data: ProjectWorkflowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update project workflow step.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission
    if not (
        project.owner_id == current_user.id or
        project.responsible_id == current_user.id or
        project.accountable_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update workflow for this project"
        )
    
    project.workflow_step = workflow_data.workflow_step
    project.last_activity_date = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return project


@router.patch("/{project_id}/metrics", response_model=ProjectResponse)
def update_project_metrics(
    project_id: UUID,
    metrics_data: ProjectMetricsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update project metrics.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if user has permission
    if not (
        project.owner_id == current_user.id or
        project.responsible_id == current_user.id or
        project.accountable_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update metrics for this project"
        )
    
    if metrics_data.primary_metric is not None:
        project.primary_metric = metrics_data.primary_metric
    if metrics_data.secondary_metrics is not None:
        project.secondary_metrics = metrics_data.secondary_metrics
    
    project.last_activity_date = datetime.utcnow()
    
    db.commit()
    db.refresh(project)
    
    return project
