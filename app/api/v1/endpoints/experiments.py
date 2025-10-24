"""Experiments API endpoints for project experiments."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.experiment import Experiment
from app.models.project import Project
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentAddUpdate,
    ExperimentResponse,
    ExperimentListResponse,
)
from app.middleware.rbac import require_permission

router = APIRouter()


@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    experiment_data: ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Create a new experiment.
    """
    # If project_id is provided, verify it exists and user has access
    if experiment_data.project_id:
        project = db.query(Project).filter(Project.id == experiment_data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Check if user has access to the project
        if not (
            project.owner_id == current_user.id or
            project.responsible_id == current_user.id or
            project.accountable_id == current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create experiments for this project"
            )
    
    experiment = Experiment(
        project_id=experiment_data.project_id,
        title=experiment_data.title,
        hypothesis=experiment_data.hypothesis,
        method=experiment_data.method,
        success_criteria=experiment_data.success_criteria,
        progress_updates=experiment_data.progress_updates,
    )
    
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    
    return experiment


@router.get("/", response_model=ExperimentListResponse)
def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    project_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List experiments with filtering and pagination.
    """
    query = db.query(Experiment)
    
    # Filter by project if specified
    if project_id:
        query = query.filter(Experiment.project_id == project_id)
    
    # Search filter
    if search:
        query = query.filter(
            Experiment.title.ilike(f"%{search}%") |
            Experiment.hypothesis.ilike(f"%{search}%")
        )
    
    # Order by creation date
    query = query.order_by(Experiment.created_at.desc())
    
    total = query.count()
    experiments = query.offset(skip).limit(limit).all()
    
    return ExperimentListResponse(
        experiments=experiments,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Get a specific experiment by ID.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    # If experiment is associated with a project, check access
    if experiment.project_id:
        project = db.query(Project).filter(Project.id == experiment.project_id).first()
        if project and not (
            project.owner_id == current_user.id or
            project.responsible_id == current_user.id or
            project.accountable_id == current_user.id or
            current_user.id in project.consulted_ids or
            current_user.id in project.informed_ids
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this experiment"
            )
    
    return experiment


@router.patch("/{experiment_id}", response_model=ExperimentResponse)
def update_experiment(
    experiment_id: UUID,
    experiment_data: ExperimentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update an experiment.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    # If experiment is associated with a project, check permission
    if experiment.project_id:
        project = db.query(Project).filter(Project.id == experiment.project_id).first()
        if project and not (
            project.owner_id == current_user.id or
            project.responsible_id == current_user.id or
            project.accountable_id == current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this experiment"
            )
    
    # Update fields
    update_data = experiment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(experiment, field, value)
    
    db.commit()
    db.refresh(experiment)
    
    return experiment


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete an experiment.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    # If experiment is associated with a project, check permission
    if experiment.project_id:
        project = db.query(Project).filter(Project.id == experiment.project_id).first()
        if project and project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this experiment"
            )
    
    db.delete(experiment)
    db.commit()
    
    return None


@router.post("/{experiment_id}/progress-update", response_model=ExperimentResponse)
def add_progress_update(
    experiment_id: UUID,
    update_data: ExperimentAddUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Add a progress update to an experiment.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    # If experiment is associated with a project, check permission
    if experiment.project_id:
        project = db.query(Project).filter(Project.id == experiment.project_id).first()
        if project and not (
            project.owner_id == current_user.id or
            project.responsible_id == current_user.id or
            project.accountable_id == current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this experiment"
            )
    
    # Add the update to the progress_updates array
    if experiment.progress_updates is None:
        experiment.progress_updates = []
    
    experiment.progress_updates.append(update_data.update)
    
    db.commit()
    db.refresh(experiment)
    
    return experiment
