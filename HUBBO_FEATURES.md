# 🚀 Hubbo Task Management System - Complete Implementation

## Overview

Hubbo is an AI-powered task management system with a complete workflow from Ideas → Projects → Tasks, featuring the RACI (Responsible, Accountable, Consulted, Informed) model for clear responsibility assignment.

---

## ✨ Core Features Implemented

### 1. **Ideas Management**
- ✅ Create, read, update, delete ideas
- ✅ RACI model assignment (Responsible, Accountable, Consulted, Informed)
- ✅ Archive/unarchive functionality
- ✅ Move ideas to projects
- ✅ Category and department tagging
- ✅ Status tracking (inbox, in_progress, completed, rejected)

### 2. **Projects Management**
- ✅ Create projects from ideas or standalone
- ✅ RACI model for team assignments
- ✅ Workflow step tracking (1-N)
- ✅ Project metrics (primary & secondary)
- ✅ Backlog categorization (business_innovation, product_development, operations)
- ✅ Archive/unarchive functionality
- ✅ Due date tracking
- ✅ Auto-generated project numbers (PRJ-00001, etc.)
- ✅ Progress tracking with task statistics

### 3. **Tasks Management**
- ✅ Full CRUD operations
- ✅ Task activities (checklist items) with done/undone toggle
- ✅ Comments system
- ✅ File attachments
- ✅ Activity log for audit trail
- ✅ Multiple responsible users
- ✅ Bulk task creation
- ✅ Status tracking (in_progress, completed, blocked, cancelled)
- ✅ Start and due dates

### 4. **Experiments**
- ✅ Create experiments linked to projects
- ✅ Track hypothesis, method, and success criteria
- ✅ Progress updates array
- ✅ Full CRUD operations

### 5. **Profiles**
- ✅ Extended user information
- ✅ Team and position tracking
- ✅ Avatar support
- ✅ Account disable/enable functionality
- ✅ Password change requirements

### 6. **Existing Features (Already Implemented)**
- ✅ JWT Authentication with refresh tokens
- ✅ RBAC (Role-Based Access Control)
- ✅ Email integration (password reset, notifications)
- ✅ AI integration (OpenAI, Anthropic, LangChain)
- ✅ File upload/download system
- ✅ Rate limiting and security headers

---

## 📊 Database Schema

### Tables Created

1. **profiles** - Extended user information
2. **ideas** - Ideas with RACI model
3. **projects** - Projects with workflow management
4. **tasks** - Tasks with full tracking
5. **task_activities** - Checklist items for tasks
6. **task_comments** - Comments on tasks
7. **task_attachments** - File attachments for tasks
8. **task_activity_log** - Audit trail for task changes
9. **task_responsible_users** - Multiple responsible users per task
10. **experiments** - Project experiments

---

## 🚀 Getting Started

### 1. Initialize Database

```bash
# Basic initialization (creates tables and default users)
python -m app.scripts.init_hubbo_db

# With sample data (includes example ideas, projects, and tasks)
python -m app.scripts.init_hubbo_db --with-sample-data
```

### 2. Start the Server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📝 API Endpoints

### Authentication & Users
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/profiles/me` - Get current user profile

### Ideas
- `POST /api/v1/ideas/` - Create idea
- `GET /api/v1/ideas/` - List ideas (with filters)
- `GET /api/v1/ideas/{id}` - Get idea details
- `PATCH /api/v1/ideas/{id}` - Update idea
- `DELETE /api/v1/ideas/{id}` - Delete idea
- `POST /api/v1/ideas/{id}/archive` - Archive/unarchive idea
- `POST /api/v1/ideas/{id}/move-to-project` - Convert idea to project

### Projects
- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/` - List projects (with filters)
- `GET /api/v1/projects/{id}` - Get project with task stats
- `PATCH /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project
- `POST /api/v1/projects/{id}/archive` - Archive/unarchive project
- `PATCH /api/v1/projects/{id}/workflow` - Update workflow step
- `PATCH /api/v1/projects/{id}/metrics` - Update metrics

### Tasks
- `POST /api/v1/tasks/` - Create task
- `POST /api/v1/tasks/bulk` - Create multiple tasks
- `GET /api/v1/tasks/` - List tasks (with filters)
- `GET /api/v1/tasks/{id}` - Get task with all details
- `PATCH /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task

#### Task Activities
- `POST /api/v1/tasks/{id}/activities` - Add activity
- `GET /api/v1/tasks/{id}/activities` - List activities
- `PATCH /api/v1/tasks/{id}/activities/{activity_id}` - Update activity (mark done/undone)
- `DELETE /api/v1/tasks/{id}/activities/{activity_id}` - Delete activity

#### Task Comments
- `POST /api/v1/tasks/{id}/comments` - Add comment
- `GET /api/v1/tasks/{id}/comments` - List comments
- `DELETE /api/v1/tasks/{id}/comments/{comment_id}` - Delete comment

#### Task Attachments
- `POST /api/v1/tasks/{id}/attachments` - Upload file
- `GET /api/v1/tasks/{id}/attachments` - List attachments
- `DELETE /api/v1/tasks/{id}/attachments/{attachment_id}` - Delete attachment

#### Task Activity Log
- `GET /api/v1/tasks/{id}/activity-log` - Get audit trail

#### Task Responsible Users
- `POST /api/v1/tasks/{id}/responsible-users` - Add responsible user
- `GET /api/v1/tasks/{id}/responsible-users` - List responsible users
- `DELETE /api/v1/tasks/{id}/responsible-users/{user_id}` - Remove responsible user

### Experiments
- `POST /api/v1/experiments/` - Create experiment
- `GET /api/v1/experiments/` - List experiments
- `GET /api/v1/experiments/{id}` - Get experiment
- `PATCH /api/v1/experiments/{id}` - Update experiment
- `DELETE /api/v1/experiments/{id}` - Delete experiment
- `POST /api/v1/experiments/{id}/progress-update` - Add progress update

### Profiles
- `POST /api/v1/profiles/` - Create profile
- `GET /api/v1/profiles/me` - Get my profile
- `GET /api/v1/profiles/{user_id}` - Get user profile
- `PATCH /api/v1/profiles/{user_id}` - Update profile
- `POST /api/v1/profiles/{user_id}/disable` - Disable profile
- `POST /api/v1/profiles/{user_id}/enable` - Enable profile

---

## 🔄 Workflow Example

### 1. Create an Idea

```json
POST /api/v1/ideas/
{
  "title": "Implement Real-time Notifications",
  "description": "Add WebSocket support for real-time notifications",
  "possible_outcome": "Users get instant updates, improving engagement by 25%",
  "category": "Feature Enhancement",
  "status": "inbox",
  "responsible_id": "user-uuid",
  "accountable_id": "manager-uuid",
  "departments": ["Engineering", "Product"]
}
```

### 2. Move Idea to Project

```json
POST /api/v1/ideas/{idea_id}/move-to-project
{
  "project_brief": "Implement real-time notification system using WebSockets",
  "desired_outcomes": "Real-time updates, 25% engagement increase, 50ms latency",
  "due_date": "2024-12-31T23:59:59Z",
  "generate_tasks_with_ai": true
}
```

### 3. Create Tasks for Project

```json
POST /api/v1/tasks/
{
  "project_id": "project-uuid",
  "title": "Setup WebSocket infrastructure",
  "description": "Configure WebSocket server and client libraries",
  "status": "in_progress",
  "assigned_to": "developer-uuid",
  "due_date": "2024-11-30T23:59:59Z",
  "activities": [
    {"title": "Research WebSocket libraries", "completed": true},
    {"title": "Setup Socket.IO server", "completed": false},
    {"title": "Implement connection handling", "completed": false}
  ]
}
```

### 4. Track Progress

```json
# Mark activity as done
PATCH /api/v1/tasks/{task_id}/activities/{activity_id}
{
  "completed": true
}

# Add comment
POST /api/v1/tasks/{task_id}/comments
{
  "content": "WebSocket server is up and running on port 3001"
}

# Upload attachment
POST /api/v1/tasks/{task_id}/attachments
[Upload file via multipart/form-data]
```

---

## 🎯 RACI Model

The RACI model is implemented across Ideas, Projects, and Tasks:

- **R**esponsible: Person who does the work
- **A**ccountable: Person ultimately answerable for the work
- **C**onsulted: People who provide input
- **I**nformed: People who are kept updated

### Example Usage

```json
{
  "responsible_id": "uuid-of-developer",
  "accountable_id": "uuid-of-manager",
  "consulted_ids": ["uuid-of-architect", "uuid-of-designer"],
  "informed_ids": ["uuid-of-stakeholder1", "uuid-of-stakeholder2"]
}
```

---

## 🔐 Permissions

New permissions added:

### Ideas
- `create_idea`
- `edit_idea`
- `delete_idea`
- `view_idea`
- `archive_idea`

### Projects
- `create_project`
- `edit_project`
- `delete_project`
- `view_project`
- `archive_project`
- `manage_project_workflow`

### Tasks
- `create_task`
- `edit_task`
- `delete_task`
- `view_task`
- `manage_task_activities`

### Experiments
- `create_experiment`
- `edit_experiment`
- `delete_experiment`
- `view_experiment`

---

## 🤖 AI Integration Points

The system is ready for AI integration at these points:

1. **Idea Generation** - Generate ideas from prompts
2. **Project Planning** - Auto-generate project briefs and outcomes
3. **Task Generation** - Create tasks from project requirements
4. **Task Breakdown** - Break down complex tasks into activities
5. **Content Enhancement** - Improve descriptions and documentation
6. **Smart Assignments** - Suggest responsible/accountable users based on skills

To integrate AI:
- Use existing AI endpoints: `/api/v1/ai/chat`
- Extend with custom prompts for each use case
- Already configured for OpenAI, Anthropic, and LangChain

---

## 📦 Default Users

After initialization, these users are available:

| Email | Password | Role | Access Level |
|-------|----------|------|--------------|
| admin@example.com | Admin123! | admin | Full access to all features |
| manager@example.com | Manager123! | manager | Project & team management |
| user@example.com | User123! | user | Standard user access |

---

## 🔍 Filtering & Search

All list endpoints support filtering:

### Ideas
- `status` - Filter by status
- `is_archived` - Show archived/active
- `category` - Filter by category
- `search` - Search in title/description

### Projects
- `status` - Filter by status
- `is_archived` - Show archived/active
- `backlog` - Filter by backlog type
- `search` - Search in title/description/project_number

### Tasks
- `status` - Filter by status
- `project_id` - Filter by project
- `idea_id` - Filter by idea
- `assigned_to` - Filter by assignee
- `search` - Search in title/description

---

## 📈 Task Activity Logging

All task changes are automatically logged:

- Task creation/updates/deletion
- Activity additions/updates/deletion
- Comments added/deleted
- Attachments uploaded/deleted
- Responsible users added/removed

Access the log:
```
GET /api/v1/tasks/{task_id}/activity-log
```

---

## 🎨 Frontend Integration Tips

### Kanban Board
- Use task `status` field for columns
- Filter tasks by `project_id`
- Drag & drop updates via `PATCH /api/v1/tasks/{id}`

### Timeline View
- Use `start_date` and `due_date` for Gantt charts
- Track progress with task activities completion

### Dashboard
- Get project stats from `GET /api/v1/projects/{id}` (includes task counts)
- Filter by `backlog` for different views
- Use `workflow_step` for pipeline visualization

---

## 🚨 Important Notes

1. **User IDs**: The system uses UUID for user IDs (not integers). Make sure your User model is updated accordingly.

2. **Relationships**: All foreign keys properly cascade on delete to maintain data integrity.

3. **Permissions**: Endpoints check permissions using existing RBAC middleware. Adjust permission names in endpoints as needed.

4. **File Storage**: Task attachments are stored in `data/task_attachments/{task_id}/`

5. **AI Integration**: The "move to project" endpoint has a placeholder for AI task generation. Implement this by calling your AI service.

---

## 🔧 Customization

### Adding Custom Fields

To add custom fields to any model:

1. Update the model in `app/models/`
2. Update the schema in `app/schemas/`
3. Create a migration or reinitialize the database
4. Update the endpoint logic if needed

### Adding Custom Endpoints

Follow the existing pattern:
1. Create endpoint in `app/api/v1/endpoints/`
2. Add router to `app/api/v1/api.py`
3. Use existing middleware for auth and permissions

---

## 📚 Next Steps

1. **Frontend Development**: Build React/Vue frontend using the API
2. **AI Integration**: Implement AI task generation and content enhancement
3. **Notifications**: Add email/push notifications for task updates
4. **Reports**: Create analytics and reporting endpoints
5. **Webhooks**: Add webhook support for external integrations
6. **Mobile App**: Use the same API for mobile applications

---

## 🤝 Support

- **API Documentation**: http://localhost:8000/docs
- **Database Schema**: Check model files in `app/models/`
- **Sample Data**: Run init script with `--with-sample-data` flag

---

**Built with ❤️ for Hubbo - Your AI-Powered Task Management System**
