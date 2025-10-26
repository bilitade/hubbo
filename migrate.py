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
    # User management (granular)
    "users:view",
    "users:create",
    "users:edit",
    "users:delete",
    "users:approve",
    "users:disable",
    "users:manage_roles",
    
    # Role management
    "roles:view",
    "roles:create",
    "roles:edit",
    "roles:delete",
    "roles:assign_permissions",
    
    # Permission management
    "permissions:view",
    "permissions:create",
    "permissions:delete",
    
    # AI features
    "ai:use",
    "ai:manage",
    
    # File operations
    "files:view",
    "files:upload",
    "files:delete",
    "files:manage_all",
    
    # Ideas
    "ideas:view",
    "ideas:create",
    "ideas:edit",
    "ideas:delete",
    "ideas:archive",
    "ideas:move_to_project",
    
    # Projects
    "projects:view",
    "projects:create",
    "projects:edit",
    "projects:delete",
    "projects:archive",
    "projects:manage_workflow",
    
    # Tasks
    "tasks:view",
    "tasks:create",
    "tasks:edit",
    "tasks:delete",
    "tasks:manage_activities",
    "tasks:assign",
    
    # Experiments
    "experiments:view",
    "experiments:create",
    "experiments:edit",
    "experiments:delete",
    
    # Legacy permissions (for backward compatibility)
    "create_user",
    "delete_user",
    "view_user",
    "edit_user",
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
        perm_dict["users:view"],
        perm_dict["users:edit"],
        perm_dict["ideas:view"],
        perm_dict["ideas:create"],
        perm_dict["ideas:edit"],
        perm_dict["ideas:archive"],
        perm_dict["ideas:move_to_project"],
        perm_dict["projects:view"],
        perm_dict["projects:create"],
        perm_dict["projects:edit"],
        perm_dict["projects:archive"],
        perm_dict["projects:manage_workflow"],
        perm_dict["tasks:view"],
        perm_dict["tasks:create"],
        perm_dict["tasks:edit"],
        perm_dict["tasks:assign"],
        perm_dict["tasks:manage_activities"],
        perm_dict["experiments:view"],
        perm_dict["experiments:create"],
        perm_dict["experiments:edit"],
        perm_dict["ai:use"],
        perm_dict["files:view"],
        perm_dict["files:upload"],
        perm_dict["files:delete"],
        perm_dict["roles:view"],
        perm_dict["permissions:view"],
    ]
    db.add(manager_role)
    
    # Team Member role - Standard user access
    team_member_role = Role(name="team_member", description="Standard team member access")
    team_member_role.permissions = [
        perm_dict["users:view"],
        perm_dict["ideas:view"],
        perm_dict["ideas:create"],
        perm_dict["ideas:edit"],
        perm_dict["projects:view"],
        perm_dict["projects:create"],
        perm_dict["projects:edit"],
        perm_dict["tasks:view"],
        perm_dict["tasks:create"],
        perm_dict["tasks:edit"],
        perm_dict["tasks:manage_activities"],
        perm_dict["experiments:view"],
        perm_dict["experiments:create"],
        perm_dict["ai:use"],
        perm_dict["files:view"],
        perm_dict["files:upload"],
    ]
    db.add(team_member_role)
    
    # Viewer role - Read-only access
    viewer_role = Role(name="viewer", description="Read-only access")
    viewer_role.permissions = [
        perm_dict["users:view"],
        perm_dict["ideas:view"],
        perm_dict["projects:view"],
        perm_dict["tasks:view"],
        perm_dict["experiments:view"],
        perm_dict["files:view"],
        perm_dict["roles:view"],
        perm_dict["permissions:view"],
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

