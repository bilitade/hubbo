"""LangChain tools for Hubbo AI Agent."""
from typing import Optional, List, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime
import json

from app.models.project import Project
from app.models.task import Task
from app.models.idea import Idea
from app.models.user import User
from app.models.experiment import Experiment


class GetProjectsInput(BaseModel):
    """Input for get_projects tool."""
    status: Optional[str] = Field(None, description="Filter by status: planning, not_started, in_progress, done")
    limit: int = Field(10, description="Maximum number of projects to return")


class GetProjectsTool(BaseTool):
    """Tool to fetch projects from the database."""
    name: str = "get_projects"
    description: str = """Get list of projects. Use this to answer questions about projects, their status, progress, etc.
    You can filter by status (planning, not_started, in_progress, done) and limit the results."""
    args_schema: type[BaseModel] = GetProjectsInput
    db: Session = None
    
    def _run(self, status: Optional[str] = None, limit: int = 10) -> str:
        """Execute the tool."""
        query = self.db.query(Project)
        
        if status:
            query = query.filter(Project.status == status)
        
        query = query.filter(Project.is_archived == False).order_by(desc(Project.updated_at)).limit(limit)
        projects = query.all()
        
        if not projects:
            return "No projects found matching the criteria."
        
        result = {
            "total_count": len(projects),
            "filter_applied": f"status={status}" if status else "all statuses",
            "projects": []
        }
        
        for p in projects:
            # Count tasks
            total_tasks = self.db.query(func.count(Task.id)).filter(Task.project_id == p.id).scalar() or 0
            done_tasks = self.db.query(func.count(Task.id)).filter(
                Task.project_id == p.id, Task.status == 'done'
            ).scalar() or 0
            in_progress_tasks = self.db.query(func.count(Task.id)).filter(
                Task.project_id == p.id, Task.status == 'in_progress'
            ).scalar() or 0
            
            # Calculate completion percentage
            completion = round((done_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1)
            
            # Get owner name
            owner_name = f"{p.owner.first_name} {p.owner.last_name}" if p.owner else "Unassigned"
            
            result["projects"].append({
                "title": p.title,
                "status": p.status,
                "description": p.description[:100] + "..." if p.description and len(p.description) > 100 else (p.description or "No description"),
                "owner": owner_name,
                "workflow_step": p.workflow_step,
                "total_tasks": total_tasks,
                "completed_tasks": done_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completion_percentage": completion,
                "due_date": str(p.due_date.date()) if p.due_date else "Not set",
                "last_activity": str(p.last_activity_date.date()) if p.last_activity_date else "N/A",
            })
        
        return json.dumps(result, indent=2)


class GetTasksInput(BaseModel):
    """Input for get_tasks tool."""
    status: Optional[str] = Field(None, description="Filter by status: unassigned, in_progress, done")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    limit: int = Field(10, description="Maximum number of tasks to return")


class GetTasksTool(BaseTool):
    """Tool to fetch tasks from the database."""
    name: str = "get_tasks"
    description: str = """Get list of tasks. Use this to answer questions about tasks, assignments, completion status, etc.
    You can filter by status (unassigned, in_progress, done) and limit the results."""
    args_schema: type[BaseModel] = GetTasksInput
    db: Session = None
    
    def _run(self, status: Optional[str] = None, project_id: Optional[str] = None, limit: int = 10) -> str:
        """Execute the tool."""
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        
        query = query.order_by(desc(Task.updated_at)).limit(limit)
        tasks = query.all()
        
        if not tasks:
            return "No tasks found matching the criteria."
        
        result = {
            "total_count": len(tasks),
            "filter_applied": {
                "status": status or "all",
                "project_id": project_id or "all"
            },
            "tasks": []
        }
        
        for t in tasks:
            assigned_user = None
            if t.assigned_to:
                user = self.db.query(User).filter(User.id == t.assigned_to).first()
                if user:
                    assigned_user = f"{user.first_name} {user.last_name}"
            
            # Get project name
            project_name = "No project"
            if t.project_id:
                project = self.db.query(Project).filter(Project.id == t.project_id).first()
                if project:
                    project_name = project.title
            
            # Check if overdue
            is_overdue = False
            days_until_due = None
            if t.due_date:
                days_until_due = (t.due_date - datetime.utcnow()).days
                is_overdue = days_until_due < 0 and t.status != 'done'
            
            result["tasks"].append({
                "title": t.title,
                "status": t.status,
                "description": t.description[:100] + "..." if t.description and len(t.description) > 100 else (t.description or "No description"),
                "assigned_to": assigned_user or "Unassigned",
                "project": project_name,
                "due_date": str(t.due_date.date()) if t.due_date else "Not set",
                "is_overdue": is_overdue,
                "days_until_due": days_until_due,
            })
        
        return json.dumps(result, indent=2)


class GetOverdueProjectsInput(BaseModel):
    """Input for get_overdue_projects tool."""
    pass


class GetOverdueProjectsTool(BaseTool):
    """Tool to fetch overdue projects."""
    name: str = "get_overdue_projects"
    description: str = """Get projects that are overdue (past their due date and not completed).
    Use this when asked about overdue projects, delayed projects, or projects behind schedule."""
    args_schema: type[BaseModel] = GetOverdueProjectsInput
    db: Session = None
    
    def _run(self) -> str:
        """Execute the tool."""
        now = datetime.utcnow()
        
        projects = self.db.query(Project).filter(
            and_(
                Project.due_date < now,
                Project.status != 'done',
                Project.is_archived == False
            )
        ).order_by(Project.due_date).all()
        
        if not projects:
            return json.dumps({
                "status": "success",
                "message": "No overdue projects found. All projects are on track!",
                "overdue_count": 0,
                "projects": []
            })
        
        result = {
            "status": "warning",
            "message": f"Found {len(projects)} overdue project(s)",
            "overdue_count": len(projects),
            "projects": []
        }
        
        for p in projects:
            days_overdue = (now - p.due_date).days
            
            # Get task completion
            total_tasks = self.db.query(func.count(Task.id)).filter(Task.project_id == p.id).scalar() or 0
            done_tasks = self.db.query(func.count(Task.id)).filter(
                Task.project_id == p.id, Task.status == 'done'
            ).scalar() or 0
            
            result["projects"].append({
                "title": p.title,
                "status": p.status,
                "due_date": str(p.due_date.date()),
                "days_overdue": days_overdue,
                "owner": f"{p.owner.first_name} {p.owner.last_name}" if p.owner else "Unassigned",
                "total_tasks": total_tasks,
                "completed_tasks": done_tasks,
                "urgency": "critical" if days_overdue > 7 else "high",
            })
        
        return json.dumps(result, indent=2)


class GetProjectStatsInput(BaseModel):
    """Input for get_project_stats tool."""
    pass


class GetProjectStatsTool(BaseTool):
    """Tool to get overall project statistics."""
    name: str = "get_project_stats"
    description: str = """Get overall statistics about all projects.
    Use this for questions about project overview, summary, or general status."""
    args_schema: type[BaseModel] = GetProjectStatsInput
    db: Session = None
    
    def _run(self) -> str:
        """Execute the tool."""
        total_projects = self.db.query(func.count(Project.id)).filter(
            Project.is_archived == False
        ).scalar() or 0
        
        planning = self.db.query(func.count(Project.id)).filter(
            Project.status == 'planning', Project.is_archived == False
        ).scalar() or 0
        
        not_started = self.db.query(func.count(Project.id)).filter(
            Project.status == 'not_started', Project.is_archived == False
        ).scalar() or 0
        
        in_progress = self.db.query(func.count(Project.id)).filter(
            Project.status == 'in_progress', Project.is_archived == False
        ).scalar() or 0
        
        done = self.db.query(func.count(Project.id)).filter(
            Project.status == 'done', Project.is_archived == False
        ).scalar() or 0
        
        # Task statistics - exclude tasks from archived projects
        total_tasks = self.db.query(func.count(Task.id)).join(
            Project, Task.project_id == Project.id
        ).filter(Project.is_archived == False).scalar() or 0
        
        tasks_done = self.db.query(func.count(Task.id)).join(
            Project, Task.project_id == Project.id
        ).filter(Task.status == 'done', Project.is_archived == False).scalar() or 0
        
        tasks_in_progress = self.db.query(func.count(Task.id)).join(
            Project, Task.project_id == Project.id
        ).filter(Task.status == 'in_progress', Project.is_archived == False).scalar() or 0
        
        tasks_unassigned = self.db.query(func.count(Task.id)).join(
            Project, Task.project_id == Project.id
        ).filter(Task.status == 'unassigned', Project.is_archived == False).scalar() or 0
        
        # Calculate percentages
        project_completion_rate = round((done / total_projects * 100) if total_projects > 0 else 0, 1)
        task_completion_rate = round((tasks_done / total_tasks * 100) if total_tasks > 0 else 0, 1)
        
        # Check for overdue projects
        now = datetime.utcnow()
        overdue_count = self.db.query(func.count(Project.id)).filter(
            and_(
                Project.due_date < now,
                Project.status != 'done',
                Project.is_archived == False
            )
        ).scalar() or 0
        
        result = {
            "overview": {
                "timestamp": str(datetime.utcnow()),
                "health_status": "healthy" if overdue_count == 0 else "needs_attention"
            },
            "projects": {
                "total": total_projects,
                "breakdown": {
                    "planning": planning,
                    "not_started": not_started,
                    "in_progress": in_progress,
                    "done": done,
                },
                "completion_rate": project_completion_rate,
                "overdue": overdue_count,
            },
            "tasks": {
                "total": total_tasks,
                "breakdown": {
                    "done": tasks_done,
                    "in_progress": tasks_in_progress,
                    "unassigned": tasks_unassigned,
                },
                "completion_rate": task_completion_rate,
            },
            "insights": {
                "active_work": in_progress + tasks_in_progress,
                "pending_work": planning + not_started + tasks_unassigned,
                "needs_attention": overdue_count > 0,
            }
        }
        
        return json.dumps(result, indent=2)


class GetUserWorkloadInput(BaseModel):
    """Input for get_user_workload tool."""
    limit: int = Field(10, description="Maximum number of users to return")


class GetUserWorkloadTool(BaseTool):
    """Tool to get user workload information."""
    name: str = "get_user_workload"
    description: str = """Get information about user workloads and task assignments.
    Use this to answer questions about who has the most tasks, team workload, or task distribution."""
    args_schema: type[BaseModel] = GetUserWorkloadInput
    db: Session = None
    
    def _run(self, limit: int = 10) -> str:
        """Execute the tool."""
        # Get users with their task counts
        users_with_tasks = self.db.query(
            User.id,
            User.first_name,
            User.last_name,
            User.position,
            User.department,
            func.count(Task.id).label('task_count')
        ).outerjoin(Task, Task.assigned_to == User.id).filter(
            User.is_active == True
        ).group_by(User.id).order_by(desc('task_count')).limit(limit).all()
        
        total_assigned_tasks = sum(u.task_count for u in users_with_tasks)
        
        result = {
            "total_team_members": len(users_with_tasks),
            "total_assigned_tasks": total_assigned_tasks,
            "workload_distribution": []
        }
        
        for user in users_with_tasks:
            # Get task breakdown
            in_progress = self.db.query(func.count(Task.id)).filter(
                Task.assigned_to == user.id,
                Task.status == 'in_progress'
            ).scalar() or 0
            
            done = self.db.query(func.count(Task.id)).filter(
                Task.assigned_to == user.id,
                Task.status == 'done'
            ).scalar() or 0
            
            unassigned = self.db.query(func.count(Task.id)).filter(
                Task.assigned_to == user.id,
                Task.status == 'unassigned'
            ).scalar() or 0
            
            # Calculate workload level
            if user.task_count >= 10:
                workload_level = "heavy"
            elif user.task_count >= 5:
                workload_level = "moderate"
            else:
                workload_level = "light"
            
            result["workload_distribution"].append({
                "name": f"{user.first_name} {user.last_name}",
                "position": user.position or "Not set",
                "department": user.department or "Not set",
                "total_tasks": user.task_count,
                "in_progress": in_progress,
                "completed": done,
                "unassigned": unassigned,
                "workload_level": workload_level,
                "completion_rate": round((done / user.task_count * 100) if user.task_count > 0 else 0, 1)
            })
        
        return json.dumps(result, indent=2)


class GetIdeasInput(BaseModel):
    """Input for get_ideas tool."""
    limit: int = Field(10, description="Maximum number of ideas to return")


class GetIdeasTool(BaseTool):
    """Tool to fetch ideas from the database."""
    name: str = "get_ideas"
    description: str = """Get list of ideas. Use this to answer questions about ideas, brainstorming, or innovation."""
    args_schema: type[BaseModel] = GetIdeasInput
    db: Session = None
    
    def _run(self, limit: int = 10) -> str:
        """Execute the tool."""
        ideas = self.db.query(Idea).filter(
            Idea.is_archived == False
        ).order_by(desc(Idea.created_at)).limit(limit).all()
        
        if not ideas:
            return "No ideas found."
        
        result = []
        for idea in ideas:
            result.append({
                "title": idea.title,
                "description": idea.description or "No description",
                "category": idea.category or "Uncategorized",
                "possible_outcome": idea.possible_outcome or "N/A",
                "created_at": str(idea.created_at),
            })
        
        return json.dumps(result, indent=2)


def create_tools(db: Session) -> List[BaseTool]:
    """Create all tools with database session."""
    return [
        GetProjectsTool(db=db),
        GetTasksTool(db=db),
        GetOverdueProjectsTool(db=db),
        GetProjectStatsTool(db=db),
        GetUserWorkloadTool(db=db),
        GetIdeasTool(db=db),
    ]

