"""
Hubbo Database Initialization Script.

This script initializes the complete Hubbo database with:
- All database tables (users, roles, permissions, profiles, ideas, projects, tasks, experiments)
- Default permissions
- Default roles
- Default users
- Sample data (optional)

Usage:
    python -m app.scripts.init_hubbo_db
    python -m app.scripts.init_hubbo_db --with-sample-data
"""
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base, import_models
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.profile import Profile
from app.core.security import hash_password


# Default permissions for Hubbo
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


def create_tables() -> None:
    """Create all database tables."""
    print("Creating database tables...")
    
    # Import all models to register them with SQLAlchemy
    import_models()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully")


def create_permissions(db: Session) -> None:
    """Create default permissions."""
    print("\nCreating permissions...")
    created_count = 0
    
    for permission_name in DEFAULT_PERMISSIONS:
        existing = db.query(Permission).filter(
            Permission.name == permission_name
        ).first()
        
        if not existing:
            permission = Permission(name=permission_name)
            db.add(permission)
            created_count += 1
    
    db.commit()
    print(f"✓ Created {created_count} new permissions (total: {len(DEFAULT_PERMISSIONS)})")


def create_roles(db: Session) -> None:
    """Create default roles."""
    print("\nCreating roles...")
    
    roles_config = [
        {
            "name": "admin",
            "description": "Full system access",
        },
        {
            "name": "manager",
            "description": "Project and team management",
        },
        {
            "name": "user",
            "description": "Standard user access",
        },
        {
            "name": "guest",
            "description": "Read-only access",
        },
    ]
    
    created_count = 0
    for role_config in roles_config:
        existing = db.query(Role).filter(Role.name == role_config["name"]).first()
        if not existing:
            role = Role(name=role_config["name"])
            db.add(role)
            created_count += 1
    
    db.commit()
    print(f"✓ Created {created_count} new roles (total: {len(roles_config)})")


def assign_permissions_to_roles(db: Session) -> None:
    """Assign permissions to roles."""
    print("\nAssigning permissions to roles...")
    
    # Build permission lookup map
    all_permissions = db.query(Permission).all()
    permission_map = {p.name: p for p in all_permissions}
    
    # Define role-permission mappings
    role_permission_map = {
        "admin": DEFAULT_PERMISSIONS,  # All permissions
        "manager": [
            "view_user",
            "edit_user",
            "use_ai",
            "user:read",
            "user:write",
            "create_idea",
            "edit_idea",
            "view_idea",
            "archive_idea",
            "create_project",
            "edit_project",
            "view_project",
            "archive_project",
            "manage_project_workflow",
            "create_task",
            "edit_task",
            "view_task",
            "manage_task_activities",
            "create_experiment",
            "edit_experiment",
            "view_experiment",
        ],
        "user": [
            "view_user",
            "use_ai",
            "user:read",
            "user:write",
            "create_idea",
            "edit_idea",
            "view_idea",
            "view_project",
            "create_task",
            "edit_task",
            "view_task",
            "manage_task_activities",
            "view_experiment",
        ],
        "guest": [
            "view_user",
            "view_idea",
            "view_project",
            "view_task",
            "view_experiment",
        ],
    }
    
    for role_name, permission_names in role_permission_map.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"⚠ Role '{role_name}' not found, skipping")
            continue
        
        permissions = [
            permission_map[name]
            for name in permission_names
            if name in permission_map
        ]
        
        role.permissions = permissions
        db.commit()
        print(f"✓ Assigned {len(permissions)} permissions to '{role_name}'")


def create_default_users(db: Session) -> None:
    """Create default users with profiles."""
    print("\nCreating default users...")
    
    default_users = [
        {
            "first_name": "Admin",
            "middle_name": "System",
            "last_name": "User",
            "role_title": "System Administrator",
            "email": "admin@example.com",
            "password": "Admin123!",
            "role": "admin",
            "is_approved": True,
            "profile": {
                "display_name": "Admin User",
                "team": "Engineering",
                "position": "Administrator",
            }
        },
        {
            "first_name": "Manager",
            "middle_name": "Test",
            "last_name": "User",
            "role_title": "Project Manager",
            "email": "manager@example.com",
            "password": "Manager123!",
            "role": "manager",
            "is_approved": True,
            "profile": {
                "display_name": "Manager User",
                "team": "Product",
                "position": "Manager",
            }
        },
        {
            "first_name": "Regular",
            "middle_name": "Test",
            "last_name": "User",
            "role_title": "Developer",
            "email": "user@example.com",
            "password": "User123!",
            "role": "user",
            "is_approved": True,
            "profile": {
                "display_name": "Regular User",
                "team": "Engineering",
                "position": "Developer",
            }
        },
    ]
    
    created_count = 0
    for user_data in default_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        
        if not existing:
            user = User(
                first_name=user_data["first_name"],
                middle_name=user_data["middle_name"],
                last_name=user_data["last_name"],
                role_title=user_data.get("role_title"),
                email=user_data["email"],
                password=hash_password(user_data["password"]),
                is_active=True,
                is_approved=user_data.get("is_approved", False)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Assign role
            role = db.query(Role).filter(Role.name == user_data["role"]).first()
            if role:
                user.roles.append(role)
                db.commit()
            
            # Create profile
            if "profile" in user_data:
                profile = Profile(
                    id=user.id,
                    display_name=user_data["profile"]["display_name"],
                    team=user_data["profile"]["team"],
                    position=user_data["profile"]["position"],
                    email=user_data["email"],
                )
                db.add(profile)
                db.commit()
            
            created_count += 1
            print(f"  - Created user: {user_data['email']} (role: {user_data['role']})")
    
    if created_count == 0:
        print("✓ All default users already exist")
    else:
        print(f"✓ Created {created_count} new users with profiles")


def create_sample_data(db: Session) -> None:
    """Create sample ideas, projects, and tasks for testing."""
    print("\nCreating sample data...")
    
    # Get admin user
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        print("⚠ Admin user not found, skipping sample data")
        return
    
    from app.models.idea import Idea
    from app.models.project import Project
    from app.models.task import Task, TaskActivity
    
    # Create sample idea
    existing_idea = db.query(Idea).filter(Idea.title == "Sample Idea: Improve User Experience").first()
    if not existing_idea:
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
        db.commit()
        print("  - Created sample idea")
    
    # Create sample project
    existing_project = db.query(Project).filter(Project.title == "Sample Project: Q1 Platform Upgrade").first()
    if not existing_project:
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
        db.commit()
        db.refresh(project)
        
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
        
        # Add activities to task
        activity1 = TaskActivity(
            task_id=task1.id,
            title="Install Docker and dependencies",
            completed=True,
        )
        activity2 = TaskActivity(
            task_id=task1.id,
            title="Configure database connections",
            completed=True,
        )
        db.add_all([activity1, activity2])
        
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
        activity3 = TaskActivity(
            task_id=task2.id,
            title="Design authentication architecture",
            completed=True,
        )
        activity4 = TaskActivity(
            task_id=task2.id,
            title="Implement JWT token generation",
            completed=False,
        )
        activity5 = TaskActivity(
            task_id=task2.id,
            title="Add refresh token rotation",
            completed=False,
        )
        db.add_all([activity3, activity4, activity5])
        
        db.commit()
        print("  - Created sample project with 2 tasks and activities")


def init_hubbo_database(with_sample_data: bool = False) -> None:
    """Initialize the complete Hubbo database."""
    print("=" * 70)
    print("HUBBO DATABASE INITIALIZATION")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        # Create all tables
        create_tables()
        
        # Create default data
        create_permissions(db)
        create_roles(db)
        assign_permissions_to_roles(db)
        create_default_users(db)
        
        # Create sample data if requested
        if with_sample_data:
            create_sample_data(db)
        
        print("\n" + "=" * 70)
        print("✓ HUBBO DATABASE INITIALIZATION COMPLETE!")
        print("=" * 70)
        print("\nDefault users created:")
        print("  - admin@example.com / Admin123! (admin)")
        print("  - manager@example.com / Manager123! (manager)")
        print("  - user@example.com / User123! (user)")
        print("\nYou can now start the application:")
        print("  uvicorn app.main:app --reload")
        print("\nAPI Documentation:")
        print("  http://localhost:8000/docs")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Check for --with-sample-data flag
    with_sample_data = "--with-sample-data" in sys.argv
    
    if with_sample_data:
        print("Note: Sample data will be created\n")
    
    init_hubbo_database(with_sample_data=with_sample_data)
