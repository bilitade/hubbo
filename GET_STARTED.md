# 🎯 Get Started with Hubbo - Step by Step

## ⚡ Quick Start (5 Minutes)

### Step 1: Initialize Database
```bash
cd /home/bilisuma/Desktop/hubbo/backend
source .venv/bin/activate
python -m app.scripts.init_hubbo_db --with-sample-data
```

### Step 2: Start Server
```bash
uvicorn app.main:app --reload
```

### Step 3: Test API
Open in browser: **http://localhost:8000/docs**

Login with:
- Email: `admin@example.com`
- Password: `Admin123!`

---

## 🧪 Run Automated Tests

```bash
# Make sure server is running first!
python test_hubbo_api.py
```

This will test the complete workflow:
- ✅ Authentication
- ✅ Create Idea
- ✅ Move to Project
- ✅ Create Tasks
- ✅ Add Activities
- ✅ Mark Activities Done
- ✅ Add Comments
- ✅ Get Activity Log
- ✅ Create Experiments
- ✅ Update Workflow

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `IMPLEMENTATION_SUMMARY.md` | Complete overview of what was built |
| `HUBBO_FEATURES.md` | Detailed feature documentation |
| `QUICK_START.md` | API examples and common operations |
| `MIGRATION_NOTES.md` | Important notes about User ID types |
| `GET_STARTED.md` | This file - quick start guide |

---

## 🔑 Default Users

| Email | Password | Role | Use For |
|-------|----------|------|---------|
| admin@example.com | Admin123! | admin | Full access, testing all features |
| manager@example.com | Manager123! | manager | Project management testing |
| user@example.com | User123! | user | Standard user testing |

---

## 🎯 Test the Complete Workflow

### 1. Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "Admin123!"}'
```

### 2. Create an Idea
```bash
curl -X POST "http://localhost:8000/api/v1/ideas/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Idea",
    "description": "This is a test idea",
    "possible_outcome": "Great results",
    "status": "inbox"
  }'
```

### 3. View in Swagger UI
Go to http://localhost:8000/docs and explore all endpoints interactively!

---

## 📊 What You Can Do

### Ideas Management
- Create, edit, delete ideas
- Assign RACI (Responsible, Accountable, Consulted, Informed)
- Archive/unarchive ideas
- Move ideas to projects

### Projects Management
- Create projects from ideas or standalone
- Track workflow steps (1-N)
- Manage metrics and KPIs
- Archive/unarchive projects
- View task statistics and progress

### Tasks Management
- Create tasks with activities (checklist)
- Mark activities as done/undone
- Add comments for collaboration
- Upload file attachments
- View complete activity log (audit trail)
- Assign multiple responsible users
- Bulk create tasks

### Experiments
- Create experiments for projects
- Track hypothesis and success criteria
- Add progress updates
- Link to projects

### Profiles
- Extended user information
- Team and position tracking
- Avatar support
- Enable/disable accounts

---

## 🚨 Important: User ID Type

⚠️ **Your schema uses UUID but the boilerplate uses Integer for user IDs.**

You must choose one approach:

### Option A: Use UUID (Recommended)
Update `app/models/user.py`:
```python
from sqlalchemy.dialects.postgresql import UUID
import uuid

id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4
)
```

### Option B: Use Integer
Update all new models to use Integer instead of UUID.

**See `MIGRATION_NOTES.md` for detailed instructions.**

---

## 🗂️ Project Structure

```
backend/
├── app/
│   ├── models/              # Database models (10 new models)
│   ├── schemas/             # Pydantic schemas (40+ schemas)
│   ├── api/v1/endpoints/    # API endpoints (60+ endpoints)
│   └── scripts/
│       └── init_hubbo_db.py # Database initialization
│
├── test_hubbo_api.py        # Automated test suite
├── IMPLEMENTATION_SUMMARY.md # Complete overview
├── HUBBO_FEATURES.md        # Feature documentation
├── QUICK_START.md           # API examples
├── MIGRATION_NOTES.md       # Migration guide
└── GET_STARTED.md           # This file
```

---

## 🎨 API Endpoints Overview

### Core Workflow
- `/api/v1/ideas/` - Ideas management (7 endpoints)
- `/api/v1/projects/` - Projects management (8 endpoints)
- `/api/v1/tasks/` - Tasks management (20+ endpoints)
- `/api/v1/experiments/` - Experiments (6 endpoints)
- `/api/v1/profiles/` - User profiles (6 endpoints)

### Existing Features
- `/api/v1/auth/` - Authentication
- `/api/v1/users/` - User management
- `/api/v1/roles/` - Role management
- `/api/v1/permissions/` - Permission management
- `/api/v1/ai/` - AI features
- `/api/v1/files/` - File management

---

## 🔍 Explore with Swagger UI

1. Go to http://localhost:8000/docs
2. Click "Authorize" button (top right)
3. Login with admin credentials
4. Try out any endpoint interactively
5. See request/response examples
6. Test different scenarios

---

## 💡 Tips for Success

1. **Start with Sample Data**: Use `--with-sample-data` flag to see examples
2. **Use Swagger UI**: Best way to explore the API
3. **Check Activity Logs**: See what's happening in tasks
4. **Test Permissions**: Login as different users
5. **Read Documentation**: Check the markdown files for details

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
uvicorn app.main:app --reload --port 8001
```

### Database errors
```bash
# Reinitialize database
python -m app.scripts.init_hubbo_db --with-sample-data
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Can't login
Make sure you initialized the database first!

---

## 📈 Next Steps

### Immediate
1. ✅ Initialize database
2. ✅ Start server
3. ✅ Run automated tests
4. ✅ Explore Swagger UI
5. ✅ Test complete workflow

### Short Term
1. Resolve User ID type (UUID vs Integer)
2. Implement AI task generation
3. Add email notifications
4. Configure file storage
5. Build frontend

### Long Term
1. Real-time features (WebSocket)
2. Advanced analytics
3. Mobile app
4. Third-party integrations
5. Advanced reporting

---

## 🎓 Learning Path

### Day 1: Setup & Basics
- Initialize database
- Explore Swagger UI
- Create ideas, projects, tasks
- Test basic CRUD operations

### Day 2: Advanced Features
- Test RACI model
- Try task activities
- Add comments and attachments
- Check activity logs

### Day 3: Integration
- Implement AI features
- Add email notifications
- Configure permissions
- Test with different users

### Week 2: Frontend
- Build React/Vue frontend
- Connect to API
- Implement UI/UX
- Deploy to production

---

## 🎉 You're Ready!

Everything is set up and ready to use. Just run:

```bash
# 1. Initialize
python -m app.scripts.init_hubbo_db --with-sample-data

# 2. Start
uvicorn app.main:app --reload

# 3. Test
python test_hubbo_api.py

# 4. Explore
# Open http://localhost:8000/docs
```

---

## 📞 Need Help?

1. **Check Documentation**: Read the markdown files
2. **Swagger UI**: Interactive API documentation
3. **Test Script**: Run automated tests to verify setup
4. **Code Comments**: All files are well-documented

---

## ✅ Checklist

- [ ] Database initialized
- [ ] Server running
- [ ] Can access Swagger UI
- [ ] Can login
- [ ] Created test idea
- [ ] Moved idea to project
- [ ] Created task with activities
- [ ] Marked activity as done
- [ ] Added comment
- [ ] Viewed activity log
- [ ] All automated tests pass

---

**Happy Building! 🚀**

Your Hubbo task management system is ready to power your AI-driven workflow!
