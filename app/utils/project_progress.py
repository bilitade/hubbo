"""Project progress calculation utilities."""
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.models.project import Project
from app.models.task import Task, TaskActivity


def calculate_project_progress(db: Session, project_id: UUID) -> Tuple[float, int, int, int, int]:
    """
    Calculate project progress based on tasks and subtasks (activities).
    
    Returns:
        Tuple of (progress_percentage, total_items, completed_items, tasks_count, completed_tasks_count)
    """
    # Get all tasks for this project
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    if not tasks:
        return 0.0, 0, 0, 0, 0
    
    tasks_count = len(tasks)
    completed_tasks_count = sum(1 for task in tasks if task.status == "done")
    
    # Calculate total items (tasks + all their activities/subtasks)
    total_items = 0
    completed_items = 0
    
    for task in tasks:
        # Get activities for this task
        activities = db.query(TaskActivity).filter(TaskActivity.task_id == task.id).all()
        
        if activities:
            # If task has activities, count each activity
            total_items += len(activities)
            completed_items += sum(1 for activity in activities if activity.completed)
        else:
            # If no activities, count the task itself
            total_items += 1
            completed_items += 1 if task.status == "done" else 0
    
    progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
    
    return round(progress_percentage, 2), total_items, completed_items, tasks_count, completed_tasks_count


def auto_update_project_status(db: Session, project: Project) -> str:
    """
    Automatically determine and update project status based on tasks.
    
    Status Rules:
    - planning: Project exists but no tasks created yet
    - not_started: Tasks exist, but none are assigned or started
    - in_progress: At least one task is assigned or in progress
    - done: All tasks are completed
    
    Returns:
        The new status
    """
    # Get all tasks for this project
    tasks = db.query(Task).filter(Task.project_id == project.id).all()
    
    # Planning: No tasks created yet
    if not tasks:
        return "planning"
    
    # Check task statuses
    all_done = all(task.status == "done" for task in tasks)
    any_in_progress = any(task.status == "in_progress" for task in tasks)
    any_assigned = any(task.assigned_to is not None for task in tasks)
    
    # Done: All tasks completed
    if all_done:
        return "done"
    
    # In Progress: At least one task assigned or in progress
    if any_in_progress or any_assigned:
        return "in_progress"
    
    # Not Started: Tasks exist but none assigned or started
    return "not_started"


def auto_update_task_status(db: Session, task: Task) -> str:
    """
    Automatically determine task status based on assignment and activities.
    
    Status Rules:
    - unassigned: Task has no one assigned to it
    - in_progress: Task is assigned to someone (work has started)
    - done: All activities are completed
    
    Returns:
        The new status
    """
    # Get all activities for this task
    activities = db.query(TaskActivity).filter(TaskActivity.task_id == task.id).all()
    
    # If task has activities, check completion
    if activities:
        completed_count = sum(1 for activity in activities if activity.completed)
        total_count = len(activities)
        
        if completed_count == total_count:
            # All activities completed = done
            return "done"
        elif task.assigned_to is not None:
            # Task is assigned = in progress (regardless of completion)
            return "in_progress"
        else:
            # Not assigned = unassigned
            return "unassigned"
    else:
        # No activities - check assignment
        if task.status == "done":
            return "done"
        elif task.assigned_to is not None:
            return "in_progress"
        else:
            return "unassigned"

