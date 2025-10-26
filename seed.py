#!/usr/bin/env python3
"""
HUBBO Database Seeding Script

Populates the database with sample data for testing and development.

Usage:
    python seed.py                  # Add sample users, projects, tasks
    python seed.py --full           # Add extensive sample data
    
Docker Usage:
    docker-compose exec backend python seed.py
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.idea import Idea
from app.models.project import Project
from app.models.task import Task, TaskActivity
from app.models.experiment import Experiment
from app.core.security import hash_password


def create_sample_users(db):
    """Create sample users for testing."""
    print("\n👤 Creating sample users...")
    
    # Get existing roles
    roles = {role.name: role for role in db.query(Role).all()}
    
    sample_users = [
        {
            "email": "manager@example.com",
            "password": "Manager123!",
            "first_name": "Jane",
            "middle_name": "Marie",
            "last_name": "Manager",
            "display_name": "Jane Manager",
            "team": "Product",
            "department": "Product Management",
            "position": "Project Manager",
            "bio": "Project manager overseeing team operations",
            "is_active": True,
            "is_approved": True,
            "role": "manager",
        },
        {
            "email": "developer@example.com",
            "password": "Dev123!",
            "first_name": "John",
            "middle_name": "Paul",
            "last_name": "Developer",
            "display_name": "John Developer",
            "team": "Engineering",
            "department": "Engineering",
            "position": "Senior Developer",
            "bio": "Full-stack developer working on core features",
            "is_active": True,
            "is_approved": True,
            "role": "team_member",
        },
        {
            "email": "designer@example.com",
            "password": "Design123!",
            "first_name": "Sarah",
            "middle_name": "Ann",
            "last_name": "Designer",
            "display_name": "Sarah Designer",
            "team": "Design",
            "department": "Product Design",
            "position": "UX/UI Designer",
            "bio": "Creating beautiful and intuitive user experiences",
            "is_active": True,
            "is_approved": True,
            "role": "team_member",
        },
        {
            "email": "guest@example.com",
            "password": "Guest123!",
            "first_name": "Guest",
            "middle_name": "Test",
            "last_name": "User",
            "display_name": "Guest User",
            "team": "External",
            "department": "External",
            "position": "Guest Observer",
            "bio": "External guest with read-only access",
            "is_active": True,
            "is_approved": True,
            "role": "viewer",
        },
    ]
    
    created_users = []
    for user_data in sample_users:
        # Check if user already exists
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"  ⚠️  User {user_data['email']} already exists, skipping")
            created_users.append(existing)
            continue
        
        role_name = user_data.pop("role")
        plain_password = user_data.pop("password")
        
        user = User(**user_data, password=hash_password(plain_password))
        if role_name in roles:
            user.roles = [roles[role_name]]
        
        db.add(user)
        created_users.append((user, plain_password))
    
    db.commit()
    
    print(f"✓ Created {len([u for u in created_users if isinstance(u, tuple)])} new users")
    
    # Print credentials
    print("\n📝 Sample User Credentials:")
    print("=" * 60)
    for item in created_users:
        if isinstance(item, tuple):
            user, password = item
            print(f"Email:    {user.email}")
            print(f"Password: {password}")
            print(f"Role:     {user.roles[0].name if user.roles else 'N/A'}")
            print("-" * 60)
    
    return [u[0] if isinstance(u, tuple) else u for u in created_users]


def create_sample_ideas(db, users):
    """Create sample ideas."""
    print("\n💡 Creating sample ideas...")
    
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        print("  ⚠️  Admin user not found, skipping ideas")
        return []
    
    sample_ideas = [
        {
            "title": "Implement Dark Mode",
            "description": "Add dark mode support to improve user experience and reduce eye strain",
            "possible_outcome": "Improved user satisfaction and accessibility",
            "category": "UI/UX Enhancement",
            "status": "inbox",
        },
        {
            "title": "Mobile App Development",
            "description": "Create native mobile apps for iOS and Android platforms",
            "possible_outcome": "Expand user base and improve mobile experience",
            "category": "Product Development",
            "status": "inbox",
        },
        {
            "title": "AI-Powered Analytics Dashboard",
            "description": "Build intelligent analytics dashboard with predictive insights",
            "possible_outcome": "Better data-driven decision making",
            "category": "AI/Analytics",
            "status": "someday",
        },
    ]
    
    created_ideas = []
    for idea_data in sample_ideas:
        idea = Idea(
            user_id=admin.id,
            owner_id=admin.id,
            responsible_id=admin.id,
            accountable_id=admin.id,
            departments=["Engineering", "Product"],
            **idea_data
        )
        db.add(idea)
        created_ideas.append(idea)
    
    db.commit()
    print(f"✓ Created {len(created_ideas)} sample ideas")
    return created_ideas


def create_sample_projects(db, users):
    """Create sample projects with tasks."""
    print("\n📁 Creating sample projects and tasks...")
    
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        print("  ⚠️  Admin user not found, skipping projects")
        return []
    
    # Project 1: Q1 Platform Upgrade
    project1 = Project(
        title="Q1 2024 Platform Upgrade",
        description="Major platform upgrade focusing on performance and new features",
        project_brief="Upgrade platform infrastructure for better performance and scalability",
        desired_outcomes="50% performance improvement, 10x scalability, 5 new features",
        project_number="PRJ-00001",
        status="in_progress",
        backlog="business_innovation",
        workflow_step=2,
        owner_id=admin.id,
        responsible_id=admin.id,
        accountable_id=admin.id,
        departments=["Engineering", "Product"],
    )
    db.add(project1)
    db.flush()
    
    # Tasks for Project 1
    task1_1 = Task(
        project_id=project1.id,
        title="Setup CI/CD Pipeline",
        description="Configure automated testing and deployment pipeline",
        status="done",
        owner_id=admin.id,
        assigned_to=admin.id,
    )
    db.add(task1_1)
    db.flush()
    
    db.add_all([
        TaskActivity(task_id=task1_1.id, title="Configure GitHub Actions", completed=True),
        TaskActivity(task_id=task1_1.id, title="Setup Docker builds", completed=True),
        TaskActivity(task_id=task1_1.id, title="Deploy to staging", completed=True),
    ])
    
    task1_2 = Task(
        project_id=project1.id,
        title="Optimize Database Queries",
        description="Improve database performance with query optimization and indexing",
        status="in_progress",
        owner_id=admin.id,
        assigned_to=admin.id,
    )
    db.add(task1_2)
    db.flush()
    
    db.add_all([
        TaskActivity(task_id=task1_2.id, title="Analyze slow queries", completed=True),
        TaskActivity(task_id=task1_2.id, title="Add database indexes", completed=False),
        TaskActivity(task_id=task1_2.id, title="Optimize ORM queries", completed=False),
    ])
    
    task1_3 = Task(
        project_id=project1.id,
        title="Implement Real-time Notifications",
        description="Add WebSocket support for real-time updates",
        status="unassigned",
        owner_id=admin.id,
    )
    db.add(task1_3)
    
    # Project 2: Marketing Website Redesign
    project2 = Project(
        title="Marketing Website Redesign",
        description="Complete redesign of marketing website with modern UI",
        project_brief="Modernize marketing website to improve conversion and brand image",
        desired_outcomes="25% increase in conversion rate, improved brand perception",
        project_number="PRJ-00002",
        status="planning",
        backlog="core_business",
        workflow_step=1,
        owner_id=admin.id,
        responsible_id=admin.id,
        accountable_id=admin.id,
        departments=["Marketing", "Design"],
    )
    db.add(project2)
    db.flush()
    
    # Tasks for Project 2
    task2_1 = Task(
        project_id=project2.id,
        title="Create Design Mockups",
        description="Design new homepage and key landing pages",
        status="in_progress",
        owner_id=admin.id,
        assigned_to=admin.id,
    )
    db.add(task2_1)
    db.flush()
    
    db.add_all([
        TaskActivity(task_id=task2_1.id, title="Research competitor websites", completed=True),
        TaskActivity(task_id=task2_1.id, title="Create wireframes", completed=True),
        TaskActivity(task_id=task2_1.id, title="Design high-fidelity mockups", completed=False),
    ])
    
    db.commit()
    print(f"✓ Created 2 projects with 4 tasks and activities")
    return [project1, project2]


def create_sample_experiments(db, users):
    """Create sample experiments."""
    print("\n🔬 Creating sample experiments...")
    
    admin = db.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        print("  ⚠️  Admin user not found, skipping experiments")
        return []
    
    sample_experiments = [
        {
            "title": "A/B Test: New CTA Button Design",
            "description": "Test new call-to-action button design to improve click-through rate",
            "hypothesis": "Larger, more prominent CTA will increase conversions by 20%",
            "status": "in_progress",
        },
        {
            "title": "Performance Test: Database Pooling",
            "description": "Test impact of connection pooling on database performance",
            "hypothesis": "Connection pooling will reduce query latency by 30%",
            "status": "completed",
        },
    ]
    
    created_experiments = []
    for exp_data in sample_experiments:
        experiment = Experiment(
            owner_id=admin.id,
            **exp_data
        )
        db.add(experiment)
        created_experiments.append(experiment)
    
    db.commit()
    print(f"✓ Created {len(created_experiments)} sample experiments")
    return created_experiments


def main():
    """Main seeding function."""
    parser = argparse.ArgumentParser(description="HUBBO Database Seeding")
    parser.add_argument("--full", action="store_true", help="Create extensive sample data")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🌱 HUBBO DATABASE SEEDING")
    print("=" * 70)
    
    if args.full:
        print("📦 Creating extensive sample data")
    print()
    
    try:
        db = SessionLocal()
        
        try:
            users = create_sample_users(db)
            ideas = create_sample_ideas(db, users)
            projects = create_sample_projects(db, users)
            experiments = create_sample_experiments(db, users)
            
            if args.full:
                # Could add more data here in full mode
                print("\n📦 Full mode - creating additional data...")
                # Add more comprehensive sample data
                pass
            
            print("\n" + "=" * 70)
            print("🎉 DATABASE SEEDING COMPLETE!")
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"  Users:       {len(users)}")
            print(f"  Ideas:       {len(ideas)}")
            print(f"  Projects:    {len(projects)}")
            print(f"  Experiments: {len(experiments)}")
            print("\n💡 Login with any user credentials shown above")
            print("=" * 70)
            print()
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


