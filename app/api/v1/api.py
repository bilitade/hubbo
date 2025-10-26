"""API v1 router aggregation."""
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    roles,
    permissions,
    ai,
    ai_project,
    ai_enhance,
    chat,
    files,
    password,
    ideas,
    projects,
    tasks,
    experiments,
)

api_router = APIRouter()

# Authentication & User Management
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(password.router, prefix="/password", tags=["Password Management"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])

# Core Features
api_router.include_router(ideas.router, prefix="/ideas", tags=["Ideas"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])

# AI Services (Modular & Separated)
api_router.include_router(ai.router, prefix="/ai", tags=["AI Assistant"])
api_router.include_router(ai_project.router, prefix="/ai/project", tags=["AI Project Generator"])
api_router.include_router(ai_enhance.router, prefix="/ai/enhance", tags=["AI Enhancers"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI Chat (Guru)"])

# Files
api_router.include_router(files.router, prefix="/files", tags=["File Storage"])

