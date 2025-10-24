# 🚀 Hubbo Quick Start Guide

## Setup (5 minutes)

### 1. Initialize Database
```bash
# Navigate to backend directory
cd /home/bilisuma/Desktop/hubbo/backend

# Activate virtual environment
source .venv/bin/activate

# Initialize database with sample data
python -m app.scripts.init_hubbo_db --with-sample-data
```

### 2. Start Server
```bash
uvicorn app.main:app --reload
```

### 3. Access API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Default Login Credentials

```
Email: admin@example.com
Password: Admin123!
```

---

## Common API Workflows

### 🔐 Authentication

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'

# Response includes access_token - use it in subsequent requests
# Authorization: Bearer <access_token>
```

### 💡 Create an Idea

```bash
curl -X POST "http://localhost:8000/api/v1/ideas/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Improve Dashboard Performance",
    "description": "Optimize database queries and add caching",
    "possible_outcome": "50% faster load times",
    "category": "Performance",
    "status": "inbox",
    "departments": ["Engineering"]
  }'
```

### 📋 List Ideas

```bash
# All ideas
curl "http://localhost:8000/api/v1/ideas/" \
  -H "Authorization: Bearer <your_token>"

# Filter by status
curl "http://localhost:8000/api/v1/ideas/?status=inbox" \
  -H "Authorization: Bearer <your_token>"

# Search
curl "http://localhost:8000/api/v1/ideas/?search=performance" \
  -H "Authorization: Bearer <your_token>"
```

### 🚀 Move Idea to Project

```bash
curl -X POST "http://localhost:8000/api/v1/ideas/{idea_id}/move-to-project" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_brief": "Comprehensive performance optimization project",
    "desired_outcomes": "50% faster load times, reduced server costs",
    "due_date": "2024-12-31T23:59:59Z",
    "generate_tasks_with_ai": false
  }'
```

### 📊 Create Project

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q4 Platform Upgrade",
    "description": "Major platform improvements",
    "project_brief": "Upgrade infrastructure and add new features",
    "desired_outcomes": "Better performance, new features, happy users",
    "status": "in_progress",
    "backlog": "business_innovation",
    "departments": ["Engineering", "Product"]
  }'
```

### ✅ Create Task

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_uuid>",
    "title": "Implement caching layer",
    "description": "Add Redis caching for frequently accessed data",
    "status": "in_progress",
    "due_date": "2024-11-30T23:59:59Z",
    "activities": [
      {"title": "Setup Redis server", "completed": false},
      {"title": "Implement cache middleware", "completed": false},
      {"title": "Add cache invalidation logic", "completed": false}
    ]
  }'
```

### ✔️ Mark Activity as Done

```bash
curl -X PATCH "http://localhost:8000/api/v1/tasks/{task_id}/activities/{activity_id}" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true
  }'
```

### 💬 Add Comment

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/comments" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Redis is configured and running on port 6379"
  }'
```

### 📎 Upload Attachment

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/{task_id}/attachments" \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@/path/to/document.pdf"
```

### 📈 Get Project with Stats

```bash
curl "http://localhost:8000/api/v1/projects/{project_id}" \
  -H "Authorization: Bearer <your_token>"

# Response includes:
# - tasks_count
# - completed_tasks_count
# - progress_percentage
```

### 🔬 Create Experiment

```bash
curl -X POST "http://localhost:8000/api/v1/experiments/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "<project_uuid>",
    "title": "Test Redis vs Memcached",
    "hypothesis": "Redis will provide better performance for our use case",
    "method": "Run load tests with both caching solutions",
    "success_criteria": "10% better response times with Redis",
    "progress_updates": []
  }'
```

---

## File Structure

```
backend/
├── app/
│   ├── models/              # Database models
│   │   ├── idea.py         # Ideas model
│   │   ├── project.py      # Projects model
│   │   ├── task.py         # Tasks & related models
│   │   ├── experiment.py   # Experiments model
│   │   └── profile.py      # Profiles model
│   │
│   ├── schemas/            # Pydantic schemas
│   │   ├── idea.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── experiment.py
│   │   └── profile.py
│   │
│   ├── api/v1/endpoints/   # API endpoints
│   │   ├── ideas.py
│   │   ├── projects.py
│   │   ├── tasks.py
│   │   ├── experiments.py
│   │   └── profiles.py
│   │
│   └── scripts/
│       └── init_hubbo_db.py  # Database initialization
│
├── HUBBO_FEATURES.md       # Complete feature documentation
└── QUICK_START.md          # This file
```

---

## Testing the API

### Using Swagger UI (Recommended)

1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Login to get token
4. Use the token for all requests
5. Try out endpoints interactively

### Using Python

```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"email": "admin@example.com", "password": "Admin123!"}
)
token = response.json()["access_token"]

# Create idea
headers = {"Authorization": f"Bearer {token}"}
idea = requests.post(
    "http://localhost:8000/api/v1/ideas/",
    headers=headers,
    json={
        "title": "New Feature Idea",
        "description": "Add dark mode support",
        "possible_outcome": "Better user experience",
        "status": "inbox"
    }
)
print(idea.json())
```

---

## Database Schema Overview

```
users (existing)
  └── profiles (extended user info)
  └── ideas (user creates ideas)
      └── projects (ideas → projects)
          ├── tasks (project tasks)
          │   ├── task_activities (checklist)
          │   ├── task_comments
          │   ├── task_attachments
          │   ├── task_activity_log (audit)
          │   └── task_responsible_users
          └── experiments (project experiments)
```

---

## Troubleshooting

### Database Issues

```bash
# Reset database
python -m app.scripts.init_hubbo_db --with-sample-data
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

```bash
# Use different port
uvicorn app.main:app --reload --port 8001
```

---

## Next Steps

1. ✅ **Explore API**: Use Swagger UI to test all endpoints
2. ✅ **Create Sample Data**: Create ideas, projects, and tasks
3. ✅ **Test Workflow**: Idea → Project → Tasks → Activities
4. ✅ **Check Activity Log**: See audit trail for tasks
5. ✅ **Try File Upload**: Attach files to tasks

---

## Key Features to Try

- ✅ **RACI Model**: Assign Responsible, Accountable, Consulted, Informed users
- ✅ **Archive**: Archive/unarchive ideas and projects
- ✅ **Workflow Steps**: Track project progress through workflow steps
- ✅ **Task Activities**: Create checklist items and mark them done
- ✅ **Comments**: Collaborate with team through comments
- ✅ **Attachments**: Upload and manage task files
- ✅ **Activity Log**: Full audit trail of all task changes
- ✅ **Bulk Operations**: Create multiple tasks at once
- ✅ **Filtering**: Filter and search across all entities

---

## Support

- **Full Documentation**: See `HUBBO_FEATURES.md`
- **API Reference**: http://localhost:8000/docs
- **Code Examples**: Check the Swagger UI for request/response examples

---

**Happy Building! 🚀**
