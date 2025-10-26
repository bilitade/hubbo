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
    chat_stream,
    files,
    password,
    ideas,
    projects,
    tasks,
    experiments,
    system_settings,
    audit_logs,
    llm_logs,
    reports,
)
from app.api.v1 import knowledge_base

api_router = APIRouter()

# Authentication & User Management
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(password.router, prefix="/password", tags=["Password Management"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["Permissions"])
api_router.include_router(system_settings.router, prefix="/settings", tags=["System Settings"])

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
api_router.include_router(chat_stream.router, prefix="/chat", tags=["AI Chat Streaming"])

# Knowledge Base & RAG
api_router.include_router(knowledge_base.router, tags=["Knowledge Base"])

# Files
api_router.include_router(files.router, prefix="/files", tags=["File Storage"])

# System Management
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(llm_logs.router, prefix="/llm-logs", tags=["LLM Logs"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

