"""Reports generation and CSV export endpoints."""
from typing import Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.project import Project
from app.models.idea import Idea
from app.models.audit_log import AuditLog
from app.models.llm_log import LLMLog

router = APIRouter()


@router.get("/tasks/csv")
def export_tasks_csv(
    status: Optional[str] = None,
    project_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export tasks to CSV.
    """
    query = db.query(Task)
    
    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if start_date:
        query = query.filter(Task.created_at >= start_date)
    if end_date:
        query = query.filter(Task.created_at <= end_date)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'ID', 'Title', 'Description', 'Status', 'Backlog',
        'Assigned To', 'Owner', 'Accountable',
        'Start Date', 'Due Date', 'Created At', 'Updated At'
    ])
    
    # Data rows
    for task in tasks:
        writer.writerow([
            str(task.id),
            task.title,
            task.description or '',
            task.status,
            task.backlog or '',
            str(task.assigned_to) if task.assigned_to else '',
            str(task.owner_id) if task.owner_id else '',
            str(task.accountable_id) if task.accountable_id else '',
            task.start_date.isoformat() if task.start_date else '',
            task.due_date.isoformat() if task.due_date else '',
            task.created_at.isoformat(),
            task.updated_at.isoformat(),
        ])
    
    # Return CSV response
    csv_content = output.getvalue()
    filename = f"tasks_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/projects/csv")
def export_projects_csv(
    status: Optional[str] = None,
    backlog: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export projects to CSV.
    """
    query = db.query(Project)
    
    # Apply filters
    if status:
        query = query.filter(Project.status == status)
    if backlog:
        query = query.filter(Project.backlog == backlog)
    if start_date:
        query = query.filter(Project.created_at >= start_date)
    if end_date:
        query = query.filter(Project.created_at <= end_date)
    
    projects = query.order_by(Project.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'ID', 'Title', 'Description', 'Status', 'Backlog', 'Workflow Step',
        'Owner', 'Responsible', 'Accountable',
        'Primary Metric', 'Due Date', 'Created At', 'Updated At'
    ])
    
    # Data rows
    for project in projects:
        writer.writerow([
            str(project.id),
            project.title,
            project.description or '',
            project.status,
            project.backlog or '',
            project.workflow_step or '',
            str(project.owner_id) if project.owner_id else '',
            str(project.responsible_id) if project.responsible_id else '',
            str(project.accountable_id) if project.accountable_id else '',
            project.primary_metric or '',
            project.due_date.isoformat() if project.due_date else '',
            project.created_at.isoformat(),
            project.updated_at.isoformat(),
        ])
    
    csv_content = output.getvalue()
    filename = f"projects_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/ideas/csv")
def export_ideas_csv(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export ideas to CSV.
    """
    query = db.query(Idea)
    
    # Apply filters
    if status:
        query = query.filter(Idea.status == status)
    if start_date:
        query = query.filter(Idea.created_at >= start_date)
    if end_date:
        query = query.filter(Idea.created_at <= end_date)
    
    ideas = query.order_by(Idea.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'ID', 'Title', 'Description', 'Possible Outcome', 'Status',
        'Category', 'Departments', 'Impact Score', 'Feasibility Score',
        'Owner', 'Created At', 'Updated At'
    ])
    
    # Data rows
    for idea in ideas:
        writer.writerow([
            str(idea.id),
            idea.title,
            idea.description or '',
            idea.possible_outcome or '',
            idea.status,
            idea.category or '',
            ','.join(idea.departments) if idea.departments else '',
            idea.impact_score or '',
            idea.feasibility_score or '',
            str(idea.owner_id) if idea.owner_id else '',
            idea.created_at.isoformat(),
            idea.updated_at.isoformat(),
        ])
    
    csv_content = output.getvalue()
    filename = f"ideas_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/user-activity/csv")
def export_user_activity_csv(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export user activity report to CSV.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get audit logs
    logs = db.query(AuditLog).filter(
        AuditLog.created_at >= cutoff_date
    ).order_by(AuditLog.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Timestamp', 'User Email', 'Action', 'Resource Type', 'Resource ID',
        'Description', 'Endpoint', 'Method', 'Status Code', 'Success', 'IP Address'
    ])
    
    # Data rows
    for log in logs:
        writer.writerow([
            log.created_at.isoformat(),
            log.user_email or 'System',
            log.action,
            log.resource_type or '',
            log.resource_id or '',
            log.description or '',
            log.endpoint or '',
            log.method or '',
            log.status_code or '',
            'Yes' if log.success else 'No',
            log.ip_address or '',
        ])
    
    csv_content = output.getvalue()
    filename = f"user_activity_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/llm-usage/csv")
def export_llm_usage_csv(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export LLM usage report to CSV.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get LLM logs
    logs = db.query(LLMLog).filter(
        LLMLog.created_at >= cutoff_date
    ).order_by(LLMLog.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Timestamp', 'Provider', 'Model', 'Feature', 'Prompt Tokens',
        'Completion Tokens', 'Total Tokens', 'Latency (ms)', 'Success',
        'Error Message', 'Estimated Cost ($)'
    ])
    
    # Data rows
    for log in logs:
        writer.writerow([
            log.created_at.isoformat(),
            log.provider,
            log.model,
            log.feature or '',
            log.prompt_tokens or 0,
            log.completion_tokens or 0,
            log.total_tokens or 0,
            log.latency_ms or 0,
            'Yes' if log.success else 'No',
            log.error_message or '',
            f"{log.estimated_cost:.6f}" if log.estimated_cost else '0.000000',
        ])
    
    csv_content = output.getvalue()
    filename = f"llm_usage_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/summary/csv")
def export_summary_report(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Export comprehensive summary report to CSV.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Create CSV with multiple sections
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Report Header
    writer.writerow(['HUBBO Platform - Summary Report'])
    writer.writerow([f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([f'Period: Last {days} days'])
    writer.writerow([])
    
    # Tasks Summary
    writer.writerow(['TASKS SUMMARY'])
    writer.writerow(['Status', 'Count'])
    
    task_counts = db.query(
        Task.status,
        func.count(Task.id).label('count')
    ).filter(
        Task.created_at >= cutoff_date
    ).group_by(Task.status).all()
    
    for status, count in task_counts:
        writer.writerow([status, count])
    writer.writerow([])
    
    # Projects Summary
    writer.writerow(['PROJECTS SUMMARY'])
    writer.writerow(['Status', 'Count'])
    
    project_counts = db.query(
        Project.status,
        func.count(Project.id).label('count')
    ).filter(
        Project.created_at >= cutoff_date
    ).group_by(Project.status).all()
    
    for status, count in project_counts:
        writer.writerow([status, count])
    writer.writerow([])
    
    # Ideas Summary
    writer.writerow(['IDEAS SUMMARY'])
    writer.writerow(['Status', 'Count'])
    
    idea_counts = db.query(
        Idea.status,
        func.count(Idea.id).label('count')
    ).filter(
        Idea.created_at >= cutoff_date
    ).group_by(Idea.status).all()
    
    for status, count in idea_counts:
        writer.writerow([status, count])
    writer.writerow([])
    
    # User Activity Summary
    writer.writerow(['USER ACTIVITY SUMMARY'])
    total_actions = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= cutoff_date
    ).scalar() or 0
    writer.writerow(['Total Actions', total_actions])
    writer.writerow([])
    
    # LLM Usage Summary
    writer.writerow(['LLM USAGE SUMMARY'])
    total_requests = db.query(func.count(LLMLog.id)).filter(
        LLMLog.created_at >= cutoff_date
    ).scalar() or 0
    total_tokens = db.query(func.sum(LLMLog.total_tokens)).filter(
        LLMLog.created_at >= cutoff_date
    ).scalar() or 0
    total_cost = db.query(func.sum(LLMLog.estimated_cost)).filter(
        LLMLog.created_at >= cutoff_date
    ).scalar() or 0
    
    writer.writerow(['Total LLM Requests', total_requests])
    writer.writerow(['Total Tokens Used', total_tokens])
    writer.writerow(['Estimated Cost ($)', f"{total_cost:.4f}" if total_cost else "0.0000"])
    
    csv_content = output.getvalue()
    filename = f"summary_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


