"""
Script to create Knowledge Base tables with pgvector extension.

Run this script to set up the KB infrastructure:
    python -m app.scripts.create_kb_tables
"""
import sys
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.base import Base, import_models


def create_pgvector_extension():
    """Create the pgvector extension in PostgreSQL."""
    print("🔧 Creating pgvector extension...")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("✅ pgvector extension created successfully")
        except Exception as e:
            print(f"❌ Error creating pgvector extension: {e}")
            print("⚠️  Make sure you're using PostgreSQL with pgvector support")
            print("   Docker: Use image 'ankane/pgvector:latest'")
            return False
    
    return True


def create_kb_tables():
    """Create Knowledge Base tables."""
    print("\n📊 Creating Knowledge Base tables...")
    
    try:
        # Import all models
        import_models()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Knowledge Base tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def verify_tables():
    """Verify that KB tables were created."""
    print("\n🔍 Verifying tables...")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('kb_documents', 'kb_chunks')
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result]
        
        if 'kb_documents' in tables and 'kb_chunks' in tables:
            print("✅ Verification successful!")
            print(f"   Found tables: {', '.join(tables)}")
            return True
        else:
            print("❌ Verification failed!")
            print(f"   Expected: kb_documents, kb_chunks")
            print(f"   Found: {', '.join(tables) if tables else 'None'}")
            return False


def main():
    """Main execution."""
    print("=" * 60)
    print("📚 Knowledge Base Setup")
    print("=" * 60)
    
    # Step 1: Create pgvector extension
    if not create_pgvector_extension():
        print("\n❌ Setup failed at pgvector extension step")
        sys.exit(1)
    
    # Step 2: Create KB tables
    if not create_kb_tables():
        print("\n❌ Setup failed at table creation step")
        sys.exit(1)
    
    # Step 3: Verify
    if not verify_tables():
        print("\n⚠️  Setup completed but verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✨ Knowledge Base setup complete!")
    print("=" * 60)
    print("\n📖 Next steps:")
    print("1. Upload documents via /api/v1/knowledge-base/upload")
    print("2. Search KB via /api/v1/knowledge-base/search")
    print("3. Use RAG with Agent via AI chat endpoints")
    print("\n💡 Tip: Check out the API docs at http://localhost:8000/docs")


if __name__ == "__main__":
    main()



