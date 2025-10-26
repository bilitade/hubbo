#!/usr/bin/env python3
"""
HUBBO Unified Database Migration Script

This script handles complete database setup for HUBBO:
- Creates PostgreSQL extensions (pgvector)
- Creates all database tables
- Sets up indexes and constraints
- Creates default roles and permissions
- Creates default admin user

Usage:
    python migrate.py                    # Full migration (drop existing tables)
    python migrate.py --no-drop          # Migration without dropping tables
    python migrate.py --with-data        # Migration + sample data
    
Docker Usage:
    docker-compose exec backend python migrate.py
"""
import sys
import argparse
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.session import engine, SessionLocal
from app.db.base import Base, import_models
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.core.security import hash_password


# ============================================================
# COMPREHENSIVE PERMISSIONS FOR HUBBO
# ============================================================
DEFAULT_PERMISSIONS = [
    # ====== USER MANAGEMENT ======
    "users:view",                   # View user list and profiles
    "users:view_own",              # View own profile
    "users:create",                # Create new users
    "users:edit",                  # Edit user details
    "users:edit_own",              # Edit own profile
    "users:delete",                # Delete users
    "users:approve",               # Approve pending users
    "users:disable",               # Disable/enable users
    "users:manage_roles",          # Assign roles to users
    "users:view_sensitive",        # View sensitive user data
    
    # ====== ROLE MANAGEMENT ======
    "roles:view",                  # View roles
    "roles:create",                # Create new roles
    "roles:edit",                  # Edit role details
    "roles:delete",                # Delete roles
    "roles:assign_permissions",    # Assign permissions to roles
    
    # ====== PERMISSION MANAGEMENT ======
    "permissions:view",            # View permissions
    "permissions:create",          # Create custom permissions
    "permissions:delete",          # Delete permissions
    
    # ====== IDEA MANAGEMENT ======
    "ideas:view",                  # View ideas
    "ideas:view_own",              # View own ideas
    "ideas:create",                # Create new ideas
    "ideas:edit",                  # Edit ideas
    "ideas:edit_own",              # Edit own ideas
    "ideas:delete",                # Delete ideas
    "ideas:delete_own",            # Delete own ideas
    "ideas:archive",               # Archive ideas
    "ideas:move_to_project",       # Convert ideas to projects
    "ideas:assign",                # Assign ideas to users
    
    # ====== PROJECT MANAGEMENT ======
    "projects:view",               # View projects
    "projects:view_own",           # View own projects
    "projects:create",             # Create new projects
    "projects:edit",               # Edit project details
    "projects:edit_own",           # Edit own projects
    "projects:delete",             # Delete projects
    "projects:delete_own",         # Delete own projects
    "projects:archive",            # Archive projects
    "projects:manage_workflow",    # Change project workflow step
    "projects:assign",             # Assign projects to users
    "projects:view_metrics",       # View project analytics
    
    # ====== TASK MANAGEMENT ======
    "tasks:view",                  # View tasks
    "tasks:view_own",              # View own assigned tasks
    "tasks:create",                # Create new tasks
    "tasks:edit",                  # Edit task details
    "tasks:edit_own",              # Edit own tasks
    "tasks:delete",                # Delete tasks
    "tasks:delete_own",            # Delete own tasks
    "tasks:assign",                # Assign tasks to users
    "tasks:manage_activities",     # Create/edit task activities
    "tasks:manage_comments",       # Add/edit task comments
    "tasks:manage_attachments",    # Upload/delete task attachments
    "tasks:change_status",         # Change task status
    
    # ====== AI FEATURES ======
    "ai:use",                      # Use any AI features
    "ai:chat",                     # Use AI chat assistant
    "ai:chat_with_kb",            # Chat with knowledge base
    "ai:enhance_idea",             # Use AI to enhance ideas
    "ai:enhance_project",          # Use AI to enhance projects
    "ai:generate_project",         # Use AI to generate project info
    "ai:generate_tasks",           # Use AI to generate tasks
    "ai:manage",                   # Full AI management
    
    # ====== FILE MANAGEMENT ======
    "files:view",                  # View files
    "files:view_own",              # View own uploaded files
    "files:upload",                # Upload files
    "files:download",              # Download files
    "files:delete",                # Delete any files
    "files:delete_own",            # Delete own files
    "files:manage_all",            # Full file management
    
    # ====== KNOWLEDGE BASE ======
    "kb:view",                     # View knowledge base documents
    "kb:upload",                   # Upload documents to KB
    "kb:delete",                   # Delete KB documents
    "kb:search",                   # Search knowledge base
    "kb:index",                    # Re-index documents
    
    # ====== CHAT MANAGEMENT ======
    "chat:view",                   # View chat history
    "chat:view_own",               # View own chats
    "chat:create",                 # Create new chats
    "chat:delete",                 # Delete chats
    "chat:delete_own",             # Delete own chats
    "chat:manage_threads",         # Manage chat threads
    
    # ====== EXPERIMENTS ======
    "experiments:view",            # View experiments
    "experiments:view_own",        # View own experiments
    "experiments:create",          # Create experiments
    "experiments:edit",            # Edit experiments
    "experiments:edit_own",        # Edit own experiments
    "experiments:delete",          # Delete experiments
    "experiments:delete_own",      # Delete own experiments
    
    # ====== SYSTEM ADMINISTRATION ======
    "system:view_audit_logs",      # View audit logs
    "system:view_llm_logs",        # View LLM logs
    "system:manage_settings",      # Manage system settings
    "system:view_settings",        # View system settings
    "system:view_reports",         # View system reports
    "system:export_data",          # Export data
    "system:view_analytics",       # View system analytics
    
    # ====== REPORTS ======
    "reports:view",                # View reports
    "reports:create",              # Create custom reports
    "reports:export",              # Export reports
    "reports:view_llm_usage",      # View LLM usage reports
    
    # ====== PASSWORD MANAGEMENT ======
    "password:reset_own",          # Reset own password
    "password:reset_others",       # Reset other users' passwords
    
    # ====== LEGACY PERMISSIONS (backward compatibility) ======
    "create_user",                 # Legacy: Create user
    "delete_user",                 # Legacy: Delete user  
    "view_user",                   # Legacy: View user
    "edit_user",                   # Legacy: Edit user
]


def create_extensions():
    """Create required PostgreSQL extensions."""
    print("🔧 Creating PostgreSQL extensions...")
    
    with engine.connect() as conn:
        try:
            # Create pgvector extension for AI/ML features
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            conn.commit()
            print("✓ Extensions created: pgvector, uuid-ossp")
        except (OperationalError, ProgrammingError) as e:
            print(f"⚠️  Extension creation warning: {e}")
            print("   Note: This is OK if extensions are already enabled")


def drop_all_tables():
    """Drop all existing tables with CASCADE."""
    print("\n🗑️  Dropping all existing tables...")
    
    with engine.connect() as conn:
        # Drop all tables in correct order to handle dependencies
        tables_to_drop = [
            "chat_messages",
            "chat_threads",
            "chats",
            "kb_chunks",
            "kb_documents",
            "task_activities",
            "tasks",
            "experiments",
            "projects",
            "ideas",
            "password_reset_tokens",
            "refresh_tokens",
            "audit_logs",
            "llm_logs",
            "system_settings",
            "user_roles",
            "role_permissions",
            "users",
            "roles",
            "permissions",
        ]
        
        for table in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            except Exception as e:
                print(f"  ⚠️  Could not drop {table}: {e}")
        
        conn.commit()
    
    print("✓ All tables dropped")


def create_all_tables():
    """Create all tables from SQLAlchemy models."""
    print("\n📊 Creating all database tables...")
    
    # Import all models
    import_models()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✓ All tables created successfully")


def create_indexes():
    """Create additional indexes for performance."""
    print("\n⚡ Creating performance indexes...")
    
    with engine.connect() as conn:
        try:
            # User indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);"))
            
            # Chat indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at DESC);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_threads_chat_id ON chat_threads(chat_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_id ON chat_messages(thread_id);"))
            
            # Project/Task indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);"))
            
            # Knowledge base indexes (with vector support)
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_documents_user_id ON kb_documents(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_kb_chunks_document_id ON kb_chunks(document_id);"))
            
            conn.commit()
            print("✓ Performance indexes created")
        except Exception as e:
            print(f"⚠️  Index creation warning: {e}")


def seed_permissions(db):
    """Create all permissions."""
    print(f"\n🔑 Creating {len(DEFAULT_PERMISSIONS)} permissions...")
    
    permissions = []
    for perm_name in DEFAULT_PERMISSIONS:
        permission = Permission(name=perm_name)
        db.add(permission)
        permissions.append(permission)
    
    db.commit()
    print(f"✓ Created {len(permissions)} permissions")
    return permissions


def seed_roles(db, permissions):
    """Create roles with permission assignments."""
    print("\n👥 Creating roles with permissions...")
    
    # Build permission lookup map
    perm_dict = {p.name: p for p in permissions}
    
    # Admin role - ALL permissions
    admin_role = Role(name="admin", description="Full system access")
    admin_role.permissions = permissions
    db.add(admin_role)
    
    # Manager role - Project and team management
    manager_role = Role(name="manager", description="Manage projects, teams, and workflows")
    manager_role.permissions = [
        # User permissions
        perm_dict["users:view"],
        perm_dict["users:edit"],
        perm_dict["users:approve"],
        # Ideas
        perm_dict["ideas:view"],
        perm_dict["ideas:view_own"],
        perm_dict["ideas:create"],
        perm_dict["ideas:edit"],
        perm_dict["ideas:edit_own"],
        perm_dict["ideas:delete_own"],
        perm_dict["ideas:archive"],
        perm_dict["ideas:move_to_project"],
        perm_dict["ideas:assign"],
        # Projects
        perm_dict["projects:view"],
        perm_dict["projects:view_own"],
        perm_dict["projects:create"],
        perm_dict["projects:edit"],
        perm_dict["projects:edit_own"],
        perm_dict["projects:delete_own"],
        perm_dict["projects:archive"],
        perm_dict["projects:manage_workflow"],
        perm_dict["projects:assign"],
        perm_dict["projects:view_metrics"],
        # Tasks
        perm_dict["tasks:view"],
        perm_dict["tasks:view_own"],
        perm_dict["tasks:create"],
        perm_dict["tasks:edit"],
        perm_dict["tasks:edit_own"],
        perm_dict["tasks:delete_own"],
        perm_dict["tasks:assign"],
        perm_dict["tasks:manage_activities"],
        perm_dict["tasks:manage_comments"],
        perm_dict["tasks:manage_attachments"],
        perm_dict["tasks:change_status"],
        # Experiments
        perm_dict["experiments:view"],
        perm_dict["experiments:view_own"],
        perm_dict["experiments:create"],
        perm_dict["experiments:edit"],
        perm_dict["experiments:edit_own"],
        perm_dict["experiments:delete_own"],
        # AI
        perm_dict["ai:use"],
        perm_dict["ai:chat"],
        perm_dict["ai:chat_with_kb"],
        perm_dict["ai:enhance_idea"],
        perm_dict["ai:enhance_project"],
        perm_dict["ai:generate_project"],
        perm_dict["ai:generate_tasks"],
        # Files & KB
        perm_dict["files:view"],
        perm_dict["files:upload"],
        perm_dict["files:download"],
        perm_dict["files:delete_own"],
        perm_dict["kb:view"],
        perm_dict["kb:upload"],
        perm_dict["kb:search"],
        # Chat
        perm_dict["chat:view_own"],
        perm_dict["chat:create"],
        perm_dict["chat:delete_own"],
        # System
        perm_dict["roles:view"],
        perm_dict["permissions:view"],
        perm_dict["reports:view"],
        perm_dict["system:view_reports"],
    ]
    db.add(manager_role)
    
    # Team Member role - Standard user access
    team_member_role = Role(name="team_member", description="Standard team member access")
    team_member_role.permissions = [
        # User permissions
        perm_dict["users:view"],
        perm_dict["users:view_own"],
        perm_dict["users:edit_own"],
        # Ideas
        perm_dict["ideas:view"],
        perm_dict["ideas:view_own"],
        perm_dict["ideas:create"],
        perm_dict["ideas:edit_own"],
        perm_dict["ideas:delete_own"],
        # Projects
        perm_dict["projects:view"],
        perm_dict["projects:view_own"],
        perm_dict["projects:create"],
        perm_dict["projects:edit_own"],
        # Tasks
        perm_dict["tasks:view"],
        perm_dict["tasks:view_own"],
        perm_dict["tasks:create"],
        perm_dict["tasks:edit_own"],
        perm_dict["tasks:manage_activities"],
        perm_dict["tasks:manage_comments"],
        perm_dict["tasks:manage_attachments"],
        # Experiments
        perm_dict["experiments:view"],
        perm_dict["experiments:view_own"],
        perm_dict["experiments:create"],
        perm_dict["experiments:edit_own"],
        # AI
        perm_dict["ai:use"],
        perm_dict["ai:chat"],
        perm_dict["ai:chat_with_kb"],
        perm_dict["ai:enhance_idea"],
        perm_dict["ai:enhance_project"],
        perm_dict["ai:generate_project"],
        perm_dict["ai:generate_tasks"],
        # Files & KB
        perm_dict["files:view"],
        perm_dict["files:view_own"],
        perm_dict["files:upload"],
        perm_dict["files:download"],
        perm_dict["files:delete_own"],
        perm_dict["kb:view"],
        perm_dict["kb:search"],
        # Chat
        perm_dict["chat:view_own"],
        perm_dict["chat:create"],
        perm_dict["chat:delete_own"],
        # Password
        perm_dict["password:reset_own"],
    ]
    db.add(team_member_role)
    
    # Viewer role - Read-only access
    viewer_role = Role(name="viewer", description="Read-only access")
    viewer_role.permissions = [
        perm_dict["users:view"],
        perm_dict["users:view_own"],
        perm_dict["ideas:view"],
        perm_dict["ideas:view_own"],
        perm_dict["projects:view"],
        perm_dict["projects:view_own"],
        perm_dict["tasks:view"],
        perm_dict["tasks:view_own"],
        perm_dict["experiments:view"],
        perm_dict["experiments:view_own"],
        perm_dict["files:view"],
        perm_dict["files:view_own"],
        perm_dict["kb:view"],
        perm_dict["kb:search"],
        perm_dict["chat:view_own"],
        perm_dict["roles:view"],
        perm_dict["permissions:view"],
        perm_dict["password:reset_own"],
    ]
    db.add(viewer_role)
    
    db.commit()
    print(f"✓ Created 4 roles (admin: {len(admin_role.permissions)} perms, "
          f"manager: {len(manager_role.permissions)} perms, "
          f"team_member: {len(team_member_role.permissions)} perms, "
          f"viewer: {len(viewer_role.permissions)} perms)")
    
    return {
        "admin": admin_role,
        "manager": manager_role,
        "team_member": team_member_role,
        "viewer": viewer_role
    }


def seed_admin_user(db, roles):
    """Create default admin user."""
    print("\n👤 Creating default admin user...")
    
    admin = User(
        email="admin@example.com",
        password=hash_password("Admin123!"),
        first_name="Admin",
        middle_name="System",
        last_name="User",
        display_name="Admin User",
        team="Engineering",
        department="IT",
        position="System Administrator",
        bio="System administrator with full access",
        is_active=True,
        is_approved=True
    )
    admin.roles = [roles["admin"]]
    
    db.add(admin)
    db.commit()
    
    print(f"✓ Admin user created: admin@example.com / Admin123!")
    return admin


def verify_migration(db):
    """Verify migration was successful."""
    print("\n✅ Verifying migration...")
    
    users_count = db.query(User).count()
    roles_count = db.query(Role).count()
    permissions_count = db.query(Permission).count()
    
    print(f"  Users: {users_count}")
    print(f"  Roles: {roles_count}")
    print(f"  Permissions: {permissions_count}")
    
    # Check admin user
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if admin:
        print(f"  Admin: {admin.full_name} - {len(admin.roles)} role(s)")
        if admin.roles:
            print(f"  Admin permissions: {len(admin.roles[0].permissions)}")
    
    print("✓ Migration verification complete")


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="HUBBO Database Migration")
    parser.add_argument("--no-drop", action="store_true", help="Skip dropping existing tables")
    parser.add_argument("--with-data", action="store_true", help="Include sample data")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 HUBBO DATABASE MIGRATION")
    print("=" * 70)
    
    if args.no_drop:
        print("⚠️  Running in ADD-ONLY mode (existing tables will not be dropped)")
    if args.with_data:
        print("📦 Sample data will be included")
    print()
    
    try:
        # Step 1: Create extensions
        create_extensions()
        
        # Step 2: Drop existing tables (unless skipped)
        if not args.no_drop:
            drop_all_tables()
        
        # Step 3: Create all tables
        create_all_tables()
        
        # Step 4: Create indexes
        create_indexes()
        
        # Step 5: Seed data
        db = SessionLocal()
        try:
            permissions = seed_permissions(db)
            roles = seed_roles(db, permissions)
            admin = seed_admin_user(db, roles)
            
            # Optional: Create sample data
            if args.with_data:
                print("\n📦 Creating sample data...")
                # You can call the populate script here
                from app.scripts.init_database import create_sample_data
                create_sample_data(db)
            
            # Verify
            verify_migration(db)
            
        finally:
            db.close()
        
        # Success message
        print("\n" + "=" * 70)
        print("🎉 DATABASE MIGRATION COMPLETE!")
        print("=" * 70)
        print("\n📝 Default Credentials:")
        print("  Email:    admin@example.com")
        print("  Password: Admin123!")
        print("\n💡 Next Steps:")
        print("  1. Start backend:  uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("  2. Start frontend: npm run dev (in frontend directory)")
        print("  3. API Docs:       http://localhost:8000/docs")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

