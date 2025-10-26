"""Create audit_logs and llm_logs tables migration."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.config.settings import Settings

def run_migration():
    """Create audit_logs and llm_logs tables."""
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    
    migration_sql = """
    -- Create audit_logs table
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id),
        user_email VARCHAR(255),
        action VARCHAR(100) NOT NULL,
        resource_type VARCHAR(100),
        resource_id VARCHAR(255),
        description TEXT,
        changes JSONB,
        endpoint VARCHAR(255),
        method VARCHAR(10),
        ip_address VARCHAR(45),
        user_agent TEXT,
        status_code INTEGER,
        success BOOLEAN NOT NULL DEFAULT TRUE,
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
    );

    -- Create indexes for audit_logs
    CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

    -- Create llm_logs table
    CREATE TABLE IF NOT EXISTS llm_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id),
        provider VARCHAR(50) NOT NULL,
        model VARCHAR(100) NOT NULL,
        prompt TEXT,
        prompt_tokens INTEGER,
        completion TEXT,
        completion_tokens INTEGER,
        total_tokens INTEGER,
        latency_ms INTEGER,
        temperature DOUBLE PRECISION,
        max_tokens INTEGER,
        success BOOLEAN NOT NULL DEFAULT TRUE,
        error_message TEXT,
        error_type VARCHAR(100),
        estimated_cost DOUBLE PRECISION,
        endpoint VARCHAR(255),
        feature VARCHAR(100),
        extra_data JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
    );

    -- Create indexes for llm_logs
    CREATE INDEX IF NOT EXISTS idx_llm_logs_user_id ON llm_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_llm_logs_provider ON llm_logs(provider);
    CREATE INDEX IF NOT EXISTS idx_llm_logs_model ON llm_logs(model);
    CREATE INDEX IF NOT EXISTS idx_llm_logs_created_at ON llm_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_llm_logs_success ON llm_logs(success);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(migration_sql))
            conn.commit()
            print("✅ Audit logs table created successfully!")
            print("✅ LLM logs table created successfully!")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("✅ Migration completed!")
            print("")
            print("Features enabled:")
            print("  ✓ Audit Logging - Track all user actions")
            print("  ✓ LLM Logging - Track AI usage and costs")
            print("  ✓ Reports - Export data as CSV")
            print("")
            print("Next steps:")
            print("  1. Restart your backend server")
            print("  2. Navigate to Reports page to download CSV reports")
            print("  3. View Audit Logs and LLM usage statistics")
            return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Running Audit & LLM Logs Migration...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    success = run_migration()
    sys.exit(0 if success else 1)

