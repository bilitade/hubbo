"""Tasks API endpoints with activities, comments, and attachments."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, exists
from uuid import UUID
from datetime import datetime
import os
import shutil

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.task import (
    Task,
    TaskActivity,
    TaskComment,
    TaskAttachment,
    TaskActivityLog,
    TaskResponsibleUser,
)
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskBulkCreate,
    TaskActivityCreate,
    TaskActivityUpdate,
    TaskActivityResponse,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskAttachmentResponse,
    TaskActivityLogResponse,
    TaskResponsibleUserCreate,
    TaskResponsibleUserResponse,
)
from app.middleware.rbac import require_permission
from app.utils.project_progress import auto_update_task_status

router = APIRouter()

# Upload directory for task attachments
UPLOAD_DIR = "data/task_attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============= TASK CRUD =============

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Create a new task with optional activities.
    Auto-determines status: unassigned if no one assigned, in_progress if assigned
    """
    # Auto-determine initial status
    initial_status = "in_progress" if task_data.assigned_to else "unassigned"
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=initial_status,
        backlog=task_data.backlog,
        idea_id=task_data.idea_id,
        project_id=task_data.project_id,
        assigned_to=task_data.assigned_to,
        owner_id=task_data.owner_id or current_user.id,
        accountable_id=task_data.accountable_id,
        responsible_role=task_data.responsible_role,
        accountable_role=task_data.accountable_role,
        start_date=task_data.start_date,
        due_date=task_data.due_date,
    )
    
    db.add(task)
    db.flush()  # Get task ID
    
    # Create activities if provided
    for activity_data in task_data.activities:
        activity = TaskActivity(
            task_id=task.id,
            title=activity_data.title,
            completed=activity_data.completed,
        )
        db.add(activity)
    
    # Log the creation
    log = TaskActivityLog(
        task_id=task.id,
        user_id=current_user.id,
        action="created",
        details=f"Task '{task.title}' created",
    )
    db.add(log)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/bulk", response_model=List[TaskResponse], status_code=status.HTTP_201_CREATED)
def create_tasks_bulk(
    bulk_data: TaskBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Create multiple tasks at once.
    """
    created_tasks = []
    
    for task_data in bulk_data.tasks:
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            backlog=task_data.backlog,
            idea_id=task_data.idea_id,
            project_id=task_data.project_id,
            assigned_to=task_data.assigned_to,
            owner_id=task_data.owner_id or current_user.id,
            accountable_id=task_data.accountable_id,
            responsible_role=task_data.responsible_role,
            accountable_role=task_data.accountable_role,
            start_date=task_data.start_date,
            due_date=task_data.due_date,
        )
        db.add(task)
        db.flush()
        
        # Create activities if provided
        for activity_data in task_data.activities:
            activity = TaskActivity(
                task_id=task.id,
                title=activity_data.title,
                completed=activity_data.completed,
            )
            db.add(activity)
        
        # Log the creation
        log = TaskActivityLog(
            task_id=task.id,
            user_id=current_user.id,
            action="created",
            details=f"Task '{task.title}' created (bulk)",
        )
        db.add(log)
        
        created_tasks.append(task)
    
    db.commit()
    
    for task in created_tasks:
        db.refresh(task)
    
    return created_tasks


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    project_id: Optional[UUID] = None,
    idea_id: Optional[UUID] = None,
    assigned_to: Optional[UUID] = None,
    search: Optional[str] = None,
    my_items_only: bool = Query(False, description="Filter to only current user's tasks"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("tasks:view")),
):
    """
    List tasks with filtering and pagination.
    Users with 'tasks:view' permission can see all tasks unless my_items_only=True.
    """
    query = db.query(Task)
    
    # Optionally filter by user's tasks
    if my_items_only:
        query = query.filter(
            or_(
                Task.assigned_to == current_user.id,
                Task.owner_id == current_user.id,
                Task.accountable_id == current_user.id,
            )
        )
    
    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if idea_id:
        query = query.filter(Task.idea_id == idea_id)
    if assigned_to:
        query = query.filter(
            or_(
                Task.assigned_to == assigned_to,
                exists()
                .where(TaskResponsibleUser.task_id == Task.id)
                .where(TaskResponsibleUser.user_id == assigned_to)
            )
        )
    if search:
        query = query.filter(
            or_(
                Task.title.ilike(f"%{search}%"),
                Task.description.ilike(f"%{search}%"),
            )
        )
    
    # Order by due date
    query = query.order_by(Task.due_date.asc().nullslast())
    
    total = query.count()
    tasks = query.offset(skip).limit(limit).all()
    
    return TaskListResponse(
        tasks=tasks,
        total=total,
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Get a specific task by ID with all details.
    Auto-updates status based on activities.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has access to this task
    if not (
        task.assigned_to == current_user.id or
        task.owner_id == current_user.id or
        task.accountable_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task"
        )
    
    # Auto-update task status based on activities
    new_status = auto_update_task_status(db, task)
    if task.status != new_status:
        task.status = new_status
        db.commit()
        db.refresh(task)
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has permission to update
    if not (
        task.assigned_to == current_user.id or
        task.owner_id == current_user.id or
        task.accountable_id == current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )
    
    # Track changes for logging
    changes = []
    update_data = task_data.model_dump(exclude_unset=True)
    assignment_changed = False
    
    for field, value in update_data.items():
        old_value = getattr(task, field)
        if old_value != value:
            changes.append(f"{field}: {old_value} -> {value}")
            setattr(task, field, value)
            if field == 'assigned_to':
                assignment_changed = True
    
    # Log the update
    if changes:
        log = TaskActivityLog(
            task_id=task.id,
            user_id=current_user.id,
            action="updated",
            details="; ".join(changes),
        )
        db.add(log)
    
    db.commit()
    db.refresh(task)
    
    # Auto-update task status if assignment changed
    if assignment_changed:
        new_status = auto_update_task_status(db, task)
        if task.status != new_status:
            task.status = new_status
            
            # Log the auto status change
            status_log = TaskActivityLog(
                task_id=task.id,
                user_id=current_user.id,
                action="status_auto_updated",
                details=f"Task status auto-updated to '{new_status}' due to assignment change",
            )
            db.add(status_log)
            
            db.commit()
            db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user has permission to delete
    if task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )
    
    db.delete(task)
    db.commit()
    
    return None


# ============= TASK ACTIVITIES =============

@router.post("/{task_id}/activities", response_model=TaskActivityResponse, status_code=status.HTTP_201_CREATED)
def create_task_activity(
    task_id: UUID,
    activity_data: TaskActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Add an activity (checklist item) to a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    activity = TaskActivity(
        task_id=task_id,
        title=activity_data.title,
        completed=activity_data.completed,
    )
    
    db.add(activity)
    
    # Log the action
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="activity_added",
        details=f"Added activity: {activity_data.title}",
    )
    db.add(log)
    
    db.commit()
    db.refresh(activity)
    
    return activity


@router.get("/{task_id}/activities", response_model=List[TaskActivityResponse])
def list_task_activities(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List all activities for a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    activities = db.query(TaskActivity).filter(TaskActivity.task_id == task_id).all()
    
    return activities


@router.patch("/{task_id}/activities/{activity_id}", response_model=TaskActivityResponse)
def update_task_activity(
    task_id: UUID,
    activity_id: UUID,
    activity_data: TaskActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Update a task activity (e.g., mark as done/undone).
    """
    activity = db.query(TaskActivity).filter(
        TaskActivity.id == activity_id,
        TaskActivity.task_id == task_id
    ).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Track changes
    changes = []
    update_data = activity_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        old_value = getattr(activity, field)
        if old_value != value:
            changes.append(f"{field}: {old_value} -> {value}")
            setattr(activity, field, value)
    
    # Log the update
    if changes:
        log = TaskActivityLog(
            task_id=task_id,
            user_id=current_user.id,
            action="activity_updated",
            details=f"Activity '{activity.title}': {'; '.join(changes)}",
        )
        db.add(log)
    
    db.commit()
    db.refresh(activity)
    
    # Auto-update task status based on activities
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        new_status = auto_update_task_status(db, task)
        if task.status != new_status:
            task.status = new_status
            
            # Log the status change
            status_log = TaskActivityLog(
                task_id=task_id,
                user_id=current_user.id,
                action="status_auto_updated",
                details=f"Task status auto-updated to '{new_status}' based on activities",
            )
            db.add(status_log)
            
            db.commit()
            db.refresh(task)
    
    return activity


@router.delete("/{task_id}/activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_activity(
    task_id: UUID,
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete a task activity.
    """
    activity = db.query(TaskActivity).filter(
        TaskActivity.id == activity_id,
        TaskActivity.task_id == task_id
    ).first()
    
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    # Log the deletion
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="activity_deleted",
        details=f"Deleted activity: {activity.title}",
    )
    db.add(log)
    
    db.delete(activity)
    db.commit()
    
    return None


# ============= TASK COMMENTS =============

@router.post("/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
def create_task_comment(
    task_id: UUID,
    comment_data: TaskCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("create_user")),
):
    """
    Add a comment to a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=comment_data.content,
    )
    
    db.add(comment)
    
    # Log the action
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="comment_added",
        details="Added a comment",
    )
    db.add(log)
    
    db.commit()
    db.refresh(comment)
    
    return comment


@router.get("/{task_id}/comments", response_model=List[TaskCommentResponse])
def list_task_comments(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List all comments for a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    comments = db.query(TaskComment).filter(
        TaskComment.task_id == task_id
    ).order_by(TaskComment.created_at.desc()).all()
    
    return comments


@router.delete("/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_comment(
    task_id: UUID,
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete a task comment.
    """
    comment = db.query(TaskComment).filter(
        TaskComment.id == comment_id,
        TaskComment.task_id == task_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    # Only the comment author can delete it
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    # Log the deletion
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="comment_deleted",
        details="Deleted a comment",
    )
    db.add(log)
    
    db.delete(comment)
    db.commit()
    
    return None


# ============= TASK ATTACHMENTS =============

@router.get("/attachments/all", response_model=List[TaskAttachmentResponse])
def list_all_attachments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List all task attachments across all tasks.
    Useful for document management page.
    """
    attachments = db.query(TaskAttachment).order_by(
        TaskAttachment.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return attachments


@router.post("/{task_id}/attachments", response_model=TaskAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_task_attachment(
    task_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Upload an attachment to a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Create task-specific directory
    task_dir = os.path.join(UPLOAD_DIR, str(task_id))
    os.makedirs(task_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(task_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create attachment record
    attachment = TaskAttachment(
        task_id=task_id,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=current_user.id,
    )
    
    db.add(attachment)
    
    # Log the action
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="attachment_uploaded",
        details=f"Uploaded file: {file.filename}",
    )
    db.add(log)
    
    db.commit()
    db.refresh(attachment)
    
    return attachment


@router.get("/{task_id}/attachments", response_model=List[TaskAttachmentResponse])
def list_task_attachments(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List all attachments for a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    attachments = db.query(TaskAttachment).filter(
        TaskAttachment.task_id == task_id
    ).all()
    
    return attachments


@router.get("/{task_id}/attachments/{attachment_id}/download")
async def download_task_attachment(
    task_id: UUID,
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Download a task attachment.
    """
    from fastapi.responses import FileResponse
    
    attachment = db.query(TaskAttachment).filter(
        TaskAttachment.id == attachment_id,
        TaskAttachment.task_id == task_id
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    if not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.mime_type
    )


@router.delete("/{task_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_attachment(
    task_id: UUID,
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("delete_user")),
):
    """
    Delete a task attachment.
    """
    attachment = db.query(TaskAttachment).filter(
        TaskAttachment.id == attachment_id,
        TaskAttachment.task_id == task_id
    ).first()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Delete file from filesystem
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
    
    # Log the deletion
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="attachment_deleted",
        details=f"Deleted file: {attachment.file_name}",
    )
    db.add(log)
    
    db.delete(attachment)
    db.commit()
    
    return None


# ============= TASK ACTIVITY LOG =============

@router.get("/{task_id}/activity-log", response_model=List[TaskActivityLogResponse])
def get_task_activity_log(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    Get activity log for a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    logs = db.query(TaskActivityLog).filter(
        TaskActivityLog.task_id == task_id
    ).order_by(TaskActivityLog.created_at.desc()).all()
    
    return logs


# ============= TASK RESPONSIBLE USERS =============

@router.post("/{task_id}/responsible-users", response_model=TaskResponsibleUserResponse, status_code=status.HTTP_201_CREATED)
def add_responsible_user(
    task_id: UUID,
    user_data: TaskResponsibleUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Add a responsible user to a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Check if user is already responsible
    existing = db.query(TaskResponsibleUser).filter(
        TaskResponsibleUser.task_id == task_id,
        TaskResponsibleUser.user_id == user_data.user_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a responsible user for this task"
        )
    
    responsible_user = TaskResponsibleUser(
        task_id=task_id,
        user_id=user_data.user_id,
    )
    
    db.add(responsible_user)
    
    # Log the action
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="responsible_user_added",
        details=f"Added responsible user: {user_data.user_id}",
    )
    db.add(log)
    
    db.commit()
    db.refresh(responsible_user)
    
    return responsible_user


@router.get("/{task_id}/responsible-users", response_model=List[TaskResponsibleUserResponse])
def list_responsible_users(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("view_user")),
):
    """
    List all responsible users for a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    responsible_users = db.query(TaskResponsibleUser).filter(
        TaskResponsibleUser.task_id == task_id
    ).all()
    
    return responsible_users


@router.delete("/{task_id}/responsible-users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_responsible_user(
    task_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("edit_user")),
):
    """
    Remove a responsible user from a task.
    """
    responsible_user = db.query(TaskResponsibleUser).filter(
        TaskResponsibleUser.task_id == task_id,
        TaskResponsibleUser.user_id == user_id
    ).first()
    
    if not responsible_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Responsible user not found"
        )
    
    # Log the action
    log = TaskActivityLog(
        task_id=task_id,
        user_id=current_user.id,
        action="responsible_user_removed",
        details=f"Removed responsible user: {user_id}",
    )
    db.add(log)
    
    db.delete(responsible_user)
    db.commit()
    
    return None
