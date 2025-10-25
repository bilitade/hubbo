# Hubbo Database Initialization Guide

## Overview
Single, unified database initialization script that creates all tables, permissions, roles, users, and profiles.

## Location
- **Script**: `app/scripts/init_database.py`
- **Shell wrapper**: `init_database.sh`

## Usage

### Method 1: Python (Recommended)
```bash
cd backend
source .venv/bin/activate
python -m app.scripts.init_database
```

### Method 2: Shell Script
```bash
cd backend
./init_database.sh
```

### With Sample Data (Projects, Tasks, Ideas, Experiments)
```bash
python -m app.scripts.init_database --with-sample-data
# OR
./init_database.sh --with-sample-data
```

### Add to Existing Database (No Table Drop)
```bash
python -m app.scripts.init_database --skip-drop
```

## What It Creates

### Database Schema
✅ All tables including:
- users, roles, permissions
- profiles
- ideas, projects, tasks, experiments
- refresh_tokens, password_reset_tokens

### Permissions (30 total)
**User Management**: create_user, delete_user, view_user, edit_user  
**Role & Permissions**: manage_roles, manage_permissions  
**AI**: use_ai, manage_ai  
**Files**: user:read, user:write  
**Ideas**: create_idea, edit_idea, delete_idea, view_idea, archive_idea  
**Projects**: create_project, edit_project, delete_project, view_project, archive_project, manage_project_workflow  
**Tasks**: create_task, edit_task, delete_task, view_task, manage_task_activities  
**Experiments**: create_experiment, edit_experiment, delete_experiment, view_experiment  

### Roles (4 total)
- **admin** (30 permissions) - Full system access
- **manager** (21 permissions) - Project and team management
- **user** (13 permissions) - Standard user access
- **guest** (5 permissions) - Read-only access

### Default Users (5 total)

| Email | Password | Role | Status |
|-------|----------|------|--------|
| admin@example.com | Admin123! | admin | Active, Approved |
| manager@example.com | Manager123! | manager | Active, Approved |
| user@example.com | User123! | user | Active, Approved |
| guest@example.com | Guest123! | guest | Active, Approved |
| inactive@example.com | Inactive123! | user | Inactive, Not Approved |

All users have profiles with team, position, and display name.

## Features

### Clean Slate
- Drops all existing tables with CASCADE
- Recreates fresh schema
- Populates with seed data

### Comprehensive
- Includes all Hubbo features (Ideas, Projects, Tasks, Experiments)
- User profiles automatically created
- Proper permission assignments per role

### Verification
- Verifies data integrity after creation
- Confirms relationships between users, roles, and permissions
- Displays summary of created entities

## Old Scripts (Removed)
- ~~`init_hubbo_db.py`~~ - Consolidated into unified script
- ~~`init_db.py`~~ - Consolidated into unified script

## Quick Start After Initialization

```bash
# 1. Start backend (from backend directory)
uvicorn app.main:app --reload

# 2. Start frontend (from frontend directory)
npm run dev

# 3. Open browser
http://localhost:5173

# 4. Login
Email: admin@example.com
Password: Admin123!
```

## API Documentation
After starting the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Database connection error
- Check PostgreSQL is running
- Verify DATABASE_URL in .env

### Import errors
- Ensure virtual environment is activated
- Check all dependencies are installed: `pip install -r requirements.txt`

### Authentication issues after init
- Clear browser localStorage and cookies
- Make sure backend server restarted after database init

---

**Last Updated**: 2025-10-24  
**Script Version**: Unified v1.0


