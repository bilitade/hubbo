"""Create system_settings table migration."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.config.settings import Settings

def run_migration():
    """Create system_settings table."""
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS system_settings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        
        -- General Settings
        app_name VARCHAR(100),
        frontend_url VARCHAR(255),
        
        -- AI Configuration
        ai_provider VARCHAR(50),
        ai_model VARCHAR(100),
        ai_temperature DOUBLE PRECISION,
        ai_max_tokens INTEGER,
        openai_api_key TEXT,
        anthropic_api_key TEXT,
        embedding_model VARCHAR(100),
        
        -- Email Configuration
        mail_server VARCHAR(255),
        mail_port INTEGER,
        mail_username VARCHAR(255),
        mail_password TEXT,
        mail_from VARCHAR(255),
        mail_from_name VARCHAR(100),
        mail_starttls BOOLEAN,
        mail_ssl_tls BOOLEAN,
        
        -- Storage Configuration
        max_upload_size INTEGER,
        upload_dir VARCHAR(255),
        vector_store_path VARCHAR(255),
        
        -- Feature Flags
        enable_streaming BOOLEAN,
        enable_agent BOOLEAN,
        enable_knowledge_base BOOLEAN,
        
        -- Metadata
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
        updated_by UUID REFERENCES users(id)
    );
    
    -- Create index on updated_at for performance
    CREATE INDEX IF NOT EXISTS idx_system_settings_updated_at ON system_settings(updated_at);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ System settings table created successfully!")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("✅ Migration completed!")
            print("")
            print("Next steps:")
            print("  1. Restart your backend server")
            print("  2. Navigate to Settings page in the frontend")
            print("  3. Configure your AI keys and email settings")
            return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running System Settings Migration...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    success = run_migration()
    sys.exit(0 if success else 1)

