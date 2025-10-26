"""Audit logging middleware to track all user actions."""
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session
from datetime import datetime
import json
import asyncio

from app.models.audit_log import AuditLog
from app.db.session import SessionLocal


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests to audit log."""
    
    # Skip audit logging for these paths
    SKIP_PATHS = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/audit-logs",  # Don't log audit log requests
        "/api/v1/llm-logs",    # Don't log LLM log requests
    ]
    
    # Skip audit logging for these methods (view actions are not critical)
    SKIP_METHODS = ["OPTIONS", "GET"]  # Skip GET requests (view actions)
    
    # Critical endpoints that should be logged even if GET
    CRITICAL_GET_PATHS = [
        "/api/v1/auth/logout",
        "/api/v1/files/download",
        "/download",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Skip certain paths and methods
        if self._should_skip(request):
            return await call_next(request)
        
        # Capture request details
        start_time = datetime.utcnow()
        
        # Call the endpoint
        response = await call_next(request)
        
        # Get user from request state if available (set by dependencies)
        user_id = None
        user_email = None
        
        if hasattr(request.state, "user"):
            user = request.state.user
            user_id = str(user.id) if hasattr(user, "id") else None
            user_email = user.email if hasattr(user, "email") else None
        
        # Log the action in background to not slow down response
        asyncio.create_task(
            self._log_action_async(
                request=request,
                response=response,
                user_id=user_id,
                user_email=user_email,
            )
        )
        
        return response
    
    def _should_skip(self, request: Request) -> bool:
        """Check if request should be skipped from audit logging."""
        path = request.url.path
        method = request.method
        
        # Check if it's a critical GET endpoint
        is_critical_get = any(critical_path in path for critical_path in self.CRITICAL_GET_PATHS)
        
        # Skip GET requests unless they're critical
        if method == "GET" and not is_critical_get:
            return True
        
        # Skip OPTIONS
        if method in ["OPTIONS"]:
            return True
        
        # Skip specific paths
        for skip_path in self.SKIP_PATHS:
            if path.startswith(skip_path):
                return True
        
        return False
    
    async def _log_action_async(
        self,
        request: Request,
        response: Response,
        user_id: Optional[str],
        user_email: Optional[str],
    ):
        """Log the action to database asynchronously."""
        db: Session = SessionLocal()
        
        try:
            # Determine action from method and path
            action = self._determine_action(request.method, request.url.path)
            resource_type, resource_id = self._extract_resource(request.url.path)
            
            audit_log = AuditLog(
                user_id=user_id,
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                endpoint=request.url.path,
                method=request.method,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                status_code=response.status_code,
                success=200 <= response.status_code < 400,
            )
            
            db.add(audit_log)
            db.commit()
        except Exception as e:
            print(f"Error logging audit entry: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _determine_action(self, method: str, path: str) -> str:
        """Determine action type from method and path."""
        # Special cases (more specific)
        if "/login" in path:
            return "login"
        if "/logout" in path:
            return "logout"
        if "/register" in path:
            return "register"
        if "/upload" in path or "/attachments" in path and method == "POST":
            return "upload_file"
        if "/download" in path:
            return "download_file"
        if "/approve" in path:
            return "approve_user"
        if "/archive" in path:
            return "archive"
        if "/password" in path:
            return "change_password"
        
        # Map HTTP methods to actions
        action_map = {
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
            "GET": "view",  # Should rarely happen due to SKIP_METHODS
        }
        
        return action_map.get(method, "action")
    
    def _extract_resource(self, path: str) -> tuple[Optional[str], Optional[str]]:
        """Extract resource type and ID from path."""
        parts = path.split("/")
        
        # Try to find resource type and ID
        resource_type = None
        resource_id = None
        
        for i, part in enumerate(parts):
            if part in ["users", "roles", "permissions", "ideas", "projects", "tasks", "experiments", "chats", "files"]:
                resource_type = part
                # Check if next part is a UUID/ID
                if i + 1 < len(parts) and parts[i + 1] and not parts[i + 1].isalpha():
                    resource_id = parts[i + 1]
                break
        
        return resource_type, resource_id

