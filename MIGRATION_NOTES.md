# 🔄 Migration Notes - Important Changes

## ⚠️ Critical: User ID Type Mismatch

### Issue
Your provided schema uses **UUID** for user IDs:
```sql
CREATE TABLE profiles (
  id uuid NOT NULL,
  CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
```

But the existing boilerplate uses **Integer** for user IDs:
```python
# app/models/user.py
id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
```

### Solution Options

#### Option 1: Update User Model to Use UUID (Recommended)

**File**: `app/models/user.py`

Change:
```python
from sqlalchemy import Column, Integer, String, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
```

To:
```python
from sqlalchemy import Column, String, Table, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4
)
```

**Also update `user_roles` table**:
```python
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)
```

#### Option 2: Keep Integer IDs (Alternative)

If you prefer to keep integer IDs, update all new models to use Integer instead of UUID:

**Files to change**:
- `app/models/profile.py`
- `app/models/idea.py`
- `app/models/project.py`
- `app/models/task.py`
- `app/models/experiment.py`

Change all:
```python
id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

To:
```python
id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
```

And change all foreign keys from `UUID(as_uuid=True)` to `Integer`.

---

## 🔧 Recommended Migration Steps

### Step 1: Backup Existing Data
```bash
# If you have existing data
pg_dump -U your_user -d hubbo > backup.sql
```

### Step 2: Choose Your Approach

**If using UUID (Recommended for new projects)**:
1. Update `app/models/user.py` as shown above
2. Update `app/models/role.py` if needed
3. Update `app/models/token.py` foreign keys
4. Update `app/models/password_reset.py` foreign keys
5. Drop and recreate database

**If using Integer**:
1. Update all new model files to use Integer
2. Update all schema files to use `int` instead of `UUID4`
3. Drop and recreate database

### Step 3: Reinitialize Database
```bash
# Drop existing database (if any)
# In PostgreSQL:
# DROP DATABASE hubbo;
# CREATE DATABASE hubbo;

# Initialize with new schema
python -m app.scripts.init_hubbo_db --with-sample-data
```

---

## 📝 Schema Adjustments Made

### 1. Fixed Syntax Errors in Your Schema

**Original**:
```sql
is_archived: BOOL NOT NULL DEFAULT FALSE  -- Invalid syntax
```

**Fixed**:
```sql
is_archived BOOL NOT NULL DEFAULT FALSE
```

### 2. Relationship Consistency

All models now properly reference `auth.users` or `users` table depending on your setup.

### 3. Array Fields

PostgreSQL ARRAY fields are properly handled:
```python
consulted_ids: Mapped[List[uuid.UUID]] = mapped_column(
    ARRAY(UUID(as_uuid=True)),
    default=list,
    nullable=False
)
```

---

## 🗃️ Database Table Creation Order

Tables are created in this order (due to foreign key dependencies):

1. `users` (existing)
2. `roles` (existing)
3. `permissions` (existing)
4. `user_roles` (existing)
5. `profiles` (new - references users)
6. `projects` (new - references users)
7. `ideas` (new - references users, projects)
8. `tasks` (new - references users, ideas, projects)
9. `task_activities` (new - references tasks)
10. `task_comments` (new - references tasks, users)
11. `task_attachments` (new - references tasks, users)
12. `task_activity_log` (new - references tasks, users)
13. `task_responsible_users` (new - references tasks, users)
14. `experiments` (new - references projects)

---

## 🔐 Authentication Considerations

### JWT Token Payload

If you change to UUID, update JWT token creation to handle UUID:

**File**: `app/core/security.py`

```python
# When creating token
payload = {
    "sub": str(user.id),  # Convert UUID to string
    "exp": expire,
}

# When decoding token
user_id = uuid.UUID(payload.get("sub"))  # Convert back to UUID
```

---

## 🧪 Testing After Migration

### 1. Test User Creation
```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "middle_name": "User",
    "last_name": "Account",
    "email": "test@example.com",
    "password": "Test123!",
    "role_title": "Developer"
  }'
```

### 2. Test Profile Creation
```bash
# Profile should auto-create with user ID
curl "http://localhost:8000/api/v1/profiles/me" \
  -H "Authorization: Bearer <token>"
```

### 3. Test Complete Workflow
```bash
# 1. Create idea
# 2. Move to project
# 3. Create task
# 4. Add activity
# 5. Mark activity done
# 6. Add comment
# 7. Upload attachment
```

---

## 📊 Performance Considerations

### UUID vs Integer

**UUID Advantages**:
- ✅ Globally unique (good for distributed systems)
- ✅ No sequential ID exposure
- ✅ Merge-friendly across databases
- ✅ Better for microservices

**UUID Disadvantages**:
- ❌ Larger storage (16 bytes vs 4 bytes)
- ❌ Slightly slower indexing
- ❌ Less human-readable

**Integer Advantages**:
- ✅ Smaller storage
- ✅ Faster indexing
- ✅ Human-readable
- ✅ Sequential ordering

**Recommendation**: Use UUID for new projects, especially if you plan to scale or use microservices.

---

## 🔄 If You Need to Migrate Existing Data

### Script Template

```python
# migrate_to_uuid.py
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
import uuid

def migrate_users_to_uuid(db: Session):
    """Migrate existing integer user IDs to UUID."""
    # This is complex and requires:
    # 1. Create new UUID column
    # 2. Generate UUIDs for existing users
    # 3. Update all foreign keys
    # 4. Drop old integer column
    # 5. Rename UUID column to 'id'
    
    # Better approach: Export data, recreate schema, reimport
    pass
```

**Recommendation**: For existing data, it's easier to:
1. Export critical data (users, roles)
2. Drop and recreate database with new schema
3. Reimport data with new UUIDs

---

## ✅ Validation Checklist

After migration, verify:

- [ ] Users can login
- [ ] Profiles are created
- [ ] Ideas can be created
- [ ] Projects can be created from ideas
- [ ] Tasks can be created
- [ ] Task activities work (mark done/undone)
- [ ] Comments can be added
- [ ] Files can be uploaded
- [ ] Activity log is recording changes
- [ ] All foreign key relationships work
- [ ] Cascade deletes work properly

---

## 🆘 Rollback Plan

If migration fails:

```bash
# Restore from backup
psql -U your_user -d hubbo < backup.sql

# Or start fresh
python -m app.scripts.init_hubbo_db --with-sample-data
```

---

## 📞 Need Help?

Common issues and solutions:

### Issue: "relation does not exist"
**Solution**: Run `python -m app.scripts.init_hubbo_db`

### Issue: "foreign key constraint violation"
**Solution**: Check that all referenced users/projects/tasks exist

### Issue: "UUID type mismatch"
**Solution**: Ensure all models use consistent ID types (all UUID or all Integer)

### Issue: "cannot import models"
**Solution**: Check `app/db/base.py` has all model imports

---

**Good luck with your migration! 🚀**
