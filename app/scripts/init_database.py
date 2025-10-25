"""
Unified Hubbo Database Initialization Script.

This script initializes the complete Hubbo database with:
- All database tables (users, roles, permissions, profiles, ideas, projects, tasks, experiments)
- Default permissions (comprehensive set)
- Default roles (admin, manager, user, guest)
- Default users with profiles
- Optional sample data for testing

Usage:
    python -m app.scripts.init_database
    python -m app.scripts.init_database --with-sample-data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.base import Base, import_models
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.profile import Profile
from app.core.security import hash_password


# ============================================================
# COMPREHENSIVE PERMISSIONS FOR HUBBO
# ============================================================
DEFAULT_PERMISSIONS = [
    # User management
    "create_user",
    "delete_user",
    "view_user",
    "edit_user",
    
    # Role & Permission management
    "manage_roles",
    "manage_permissions",
    
    # AI features
    "use_ai",
    "manage_ai",
    
    # File operations
    "user:read",
    "user:write",
    
    # Ideas
    "create_idea",
    "edit_idea",
    "delete_idea",
    "view_idea",
    "archive_idea",
    
    # Projects
    "create_project",
    "edit_project",
    "delete_project",
    "view_project",
    "archive_project",
    "manage_project_workflow",
    
    # Tasks
    "create_task",
    "edit_task",
    "delete_task",
    "view_task",
    "manage_task_activities",
    
    # Experiments
    "create_experiment",
    "edit_experiment",
    "delete_experiment",
    "view_experiment",
]


def drop_all_tables():
    """Drop all existing tables with CASCADE."""
    print("🗑️  Dropping all existing tables...")
    with engine.connect() as conn:
        # Drop all tables in correct order to handle dependencies
        tables_to_drop = [
            "task_activities",
            "tasks",
            "experiments",
            "projects",
            "ideas",
            "profiles",
            "password_reset_tokens",
            "refresh_tokens",
            "user_roles",
            "role_permissions",
            "users",
            "roles",
            "permissions",
        ]
        
        for table in tables_to_drop:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        
        conn.commit()
    print("✓ All tables dropped")


def create_all_tables():
    """Create all tables."""
    print("\n📊 Creating all tables...")
    import_models()
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created")


def create_permissions(db: Session):
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


def create_roles(db: Session, permissions: list):
    """Create roles with permission assignments."""
    print("\n👥 Creating roles with permissions...")
    
    # Build permission lookup map
    perm_dict = {p.name: p for p in permissions}
    
    # Admin role - ALL permissions
    admin_role = Role(name="admin")
    admin_role.permissions = permissions
    db.add(admin_role)
    
    # Manager role - Project and team management
    manager_role = Role(name="manager")
    manager_role.permissions = [
        perm_dict["view_user"],
        perm_dict["edit_user"],
        perm_dict["use_ai"],
        perm_dict["user:read"],
        perm_dict["user:write"],
        perm_dict["create_idea"],
        perm_dict["edit_idea"],
        perm_dict["view_idea"],
        perm_dict["archive_idea"],
        perm_dict["create_project"],
        perm_dict["edit_project"],
        perm_dict["view_project"],
        perm_dict["archive_project"],
        perm_dict["manage_project_workflow"],
        perm_dict["create_task"],
        perm_dict["edit_task"],
        perm_dict["view_task"],
        perm_dict["manage_task_activities"],
        perm_dict["create_experiment"],
        perm_dict["edit_experiment"],
        perm_dict["view_experiment"],
    ]
    db.add(manager_role)
    
    # User role - Standard user access
    user_role = Role(name="user")
    user_role.permissions = [
        perm_dict["view_user"],
        perm_dict["use_ai"],
        perm_dict["user:read"],
        perm_dict["user:write"],
        perm_dict["create_idea"],
        perm_dict["edit_idea"],
        perm_dict["view_idea"],
        perm_dict["view_project"],
        perm_dict["create_task"],
        perm_dict["edit_task"],
        perm_dict["view_task"],
        perm_dict["manage_task_activities"],
        perm_dict["view_experiment"],
    ]
    db.add(user_role)
    
    # Guest role - Read-only access
    guest_role = Role(name="guest")
    guest_role.permissions = [
        perm_dict["view_user"],
        perm_dict["view_idea"],
        perm_dict["view_project"],
        perm_dict["view_task"],
        perm_dict["view_experiment"],
    ]
    db.add(guest_role)
    
    db.commit()
    print(f"✓ Created 4 roles (admin: {len(admin_role.permissions)} perms, "
          f"manager: {len(manager_role.permissions)} perms, "
          f"user: {len(user_role.permissions)} perms, "
          f"guest: {len(guest_role.permissions)} perms)")
    
    return {
        "admin": admin_role,
        "manager": manager_role,
        "user": user_role,
        "guest": guest_role
    }


def create_users(db: Session, roles: dict):
    """Create default users with profiles."""
    print("\n👤 Creating users with profiles...")
    
    users_data = [
        {
            "email": "admin@example.com",
            "password": "Admin123!",
            "first_name": "Admin",
            "middle_name": "System",
            "last_name": "User",
            "role_title": "System Administrator",
            "is_active": True,
            "is_approved": True,
            "roles": [roles["admin"]],
            "profile": {
                "display_name": "Admin User",
                "team": "Engineering",
                "position": "System Administrator",
            }
        },
        {
            "email": "manager@example.com",
            "password": "Manager123!",
            "first_name": "Manager",
            "middle_name": "Test",
            "last_name": "User",
            "role_title": "Project Manager",
            "is_active": True,
            "is_approved": True,
            "roles": [roles["manager"]],
            "profile": {
                "display_name": "Manager User",
                "team": "Product",
                "position": "Project Manager",
            }
        },
        {
            "email": "user@example.com",
            "password": "User123!",
            "first_name": "Regular",
            "middle_name": "Test",
            "last_name": "User",
            "role_title": "Developer",
            "is_active": True,
            "is_approved": True,
            "roles": [roles["user"]],
            "profile": {
                "display_name": "Regular User",
                "team": "Engineering",
                "position": "Developer",
            }
        },
        {
            "email": "guest@example.com",
            "password": "Guest123!",
            "first_name": "Guest",
            "middle_name": "Test",
            "last_name": "User",
            "role_title": "Guest User",
            "is_active": True,
            "is_approved": True,
            "roles": [roles["guest"]],
            "profile": {
                "display_name": "Guest User",
                "team": "External",
                "position": "Guest",
            }
        },
        {
            "email": "inactive@example.com",
            "password": "Inactive123!",
            "first_name": "Inactive",
            "middle_name": "Test",
            "last_name": "User",
            "role_title": "Inactive Account",
            "is_active": False,
            "is_approved": False,
            "roles": [roles["user"]],
            "profile": {
                "display_name": "Inactive User",
                "team": "None",
                "position": "Inactive",
            }
        }
    ]
    
    users = []
    for user_data in users_data:
        # Extract and store password for printing later
        plain_password = user_data.pop("password")
        
        # Extract roles and profile
        user_roles = user_data.pop("roles")
        profile_data = user_data.pop("profile")
        
        # Hash password
        user_data["password"] = hash_password(plain_password)
        
        # Create user
        user = User(**user_data)
        user.roles = user_roles
        
        db.add(user)
        db.flush()  # Get user.id for profile
        
        # Create profile
        profile = Profile(
            id=user.id,
            display_name=profile_data["display_name"],
            team=profile_data["team"],
            position=profile_data["position"],
            email=user.email,
        )
        db.add(profile)
        
        users.append((user, plain_password))
    
    db.commit()
    print(f"✓ Created {len(users)} users with profiles")
    
    # Print credentials
    print("\n📝 User Credentials:")
    print("=" * 60)
    for user, password in users:
        print(f"Email: {user.email}")
        print(f"Password: {password}")
        print(f"Role: {user.roles[0].name if user.roles else 'N/A'}")
        print("-" * 60)
    
    return [u for u, _ in users]


def create_sample_data(db: Session):
    """Create sample ideas, projects, tasks, and experiments."""
    print("\n📦 Creating sample data...")
    
    # Get admin user
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        print("⚠ Admin user not found, skipping sample data")
        return
    
    from app.models.idea import Idea
    from app.models.project import Project
    from app.models.task import Task, TaskActivity
    from app.models.experiment import Experiment
    
    # Create sample idea
    idea = Idea(
        user_id=admin.id,
        title="Sample Idea: Improve User Experience",
        description="Enhance the overall user experience by implementing modern UI patterns and improving navigation.",
        possible_outcome="Increased user satisfaction and engagement by 30%",
        category="Product Enhancement",
        status="inbox",
        owner_id=admin.id,
        responsible_id=admin.id,
        accountable_id=admin.id,
        departments=["Product", "Engineering"],
    )
    db.add(idea)
    db.flush()
    print("  ✓ Created sample idea")
    
    # Create sample project
    project = Project(
        title="Sample Project: Q1 Platform Upgrade",
        description="Upgrade the platform infrastructure and implement new features for Q1.",
        project_brief="Major platform upgrade focusing on performance, scalability, and new features.",
        desired_outcomes="Improved performance by 50%, support for 10x more users, 5 new features launched.",
        project_number="PRJ-00001",
        status="in_progress",
        backlog="business_innovation",
        workflow_step=2,
        owner_id=admin.id,
        responsible_id=admin.id,
        accountable_id=admin.id,
        departments=["Engineering", "Product"],
    )
    db.add(project)
    db.flush()
    print("  ✓ Created sample project")
    
    # Create sample tasks for the project
    task1 = Task(
        project_id=project.id,
        title="Setup development environment",
        description="Configure development environment with all necessary tools and dependencies.",
        status="completed",
        owner_id=admin.id,
        assigned_to=admin.id,
    )
    db.add(task1)
    db.flush()
    
    # Add activities to task1
    db.add_all([
        TaskActivity(task_id=task1.id, title="Install Docker and dependencies", completed=True),
        TaskActivity(task_id=task1.id, title="Configure database connections", completed=True),
    ])
    
    task2 = Task(
        project_id=project.id,
        title="Implement new authentication flow",
        description="Implement OAuth2 authentication with JWT tokens.",
        status="in_progress",
        owner_id=admin.id,
        assigned_to=admin.id,
    )
    db.add(task2)
    db.flush()
    
    # Add activities to task2
    db.add_all([
        TaskActivity(task_id=task2.id, title="Design authentication architecture", completed=True),
        TaskActivity(task_id=task2.id, title="Implement JWT token generation", completed=False),
        TaskActivity(task_id=task2.id, title="Add refresh token rotation", completed=False),
    ])
    
    print("  ✓ Created 2 sample tasks with activities")
    
    # Create sample experiment
    experiment = Experiment(
        title="A/B Test: New Landing Page Design",
        description="Test new landing page design to improve conversion rates.",
        hypothesis="New design will increase conversion by 25%",
        status="in_progress",
        owner_id=admin.id,
    )
    db.add(experiment)
    print("  ✓ Created sample experiment")
    
    db.commit()
    print("✓ Sample data created successfully")


def verify_data(db: Session):
    """Verify all data was created correctly."""
    print("\n✅ Verifying database...")
    
    users_count = db.query(User).count()
    roles_count = db.query(Role).count()
    permissions_count = db.query(Permission).count()
    profiles_count = db.query(Profile).count()
    
    print(f"  Users: {users_count}")
    print(f"  Roles: {roles_count}")
    print(f"  Permissions: {permissions_count}")
    print(f"  Profiles: {profiles_count}")
    
    # Check relationships
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if admin:
        print(f"  Admin user has {len(admin.roles)} role(s)")
        if admin.roles:
            print(f"  Admin role has {len(admin.roles[0].permissions)} permission(s)")
        
        # Check if profile exists
        profile = db.query(Profile).filter(Profile.id == admin.id).first()
        if profile:
            print(f"  Admin profile: {profile.display_name} - {profile.position}")
    
    print("✓ Database verification complete")


def main():
    """Main initialization function."""
    print("=" * 70)
    print("🚀 HUBBO DATABASE INITIALIZATION")
    print("=" * 70)
    
    # Check for flags
    with_sample_data = "--with-sample-data" in sys.argv
    skip_drop = "--skip-drop" in sys.argv
    
    if with_sample_data:
        print("📦 Sample data will be created")
    if skip_drop:
        print("⚠️  Skipping table drop (adding to existing database)")
    print()
    
    try:
        # Step 1: Drop existing tables (unless skipped)
        if not skip_drop:
         drop_all_tables()
        
        # Step 2: Create all tables
         create_all_tables()
        
        # Step 3: Create data in correct order
        db = SessionLocal()
        
        try:
            # Order matters for foreign key integrity!
            permissions = create_permissions(db)
            roles = create_roles(db, permissions)
            users = create_users(db, roles)
            
            # Create sample data if requested
            if with_sample_data:
                create_sample_data(db)
            
            # Step 4: Verify
            verify_data(db)
            
            print("\n" + "=" * 70)
            print("🎉 HUBBO DATABASE INITIALIZED SUCCESSFULLY!")
            print("=" * 70)
            print("\n💡 Quick Start:")
            print("  1. Start backend:  uvicorn app.main:app --reload")
            print("  2. Start frontend: npm run dev (in frontend directory)")
            print("  3. Visit:          http://localhost:5173")
            print("  4. Login with:     admin@example.com / Admin123!")
            print("\n📚 API Documentation:")
            print("  http://localhost:8000/docs")
            print("=" * 70)
            print()
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
