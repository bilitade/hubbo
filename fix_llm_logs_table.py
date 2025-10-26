"""Fix llm_logs table by dropping and recreating with correct column name."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.config.settings import Settings

def fix_tables():
    """Drop and recreate llm_logs table with correct column name."""
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    
    migration_sql = """
    -- Drop existing table if it has the wrong column
    DROP TABLE IF EXISTS llm_logs CASCADE;
    
    -- Create llm_logs table with correct column name (extra_data instead of metadata)
    CREATE TABLE llm_logs (
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
    CREATE INDEX idx_llm_logs_user_id ON llm_logs(user_id);
    CREATE INDEX idx_llm_logs_provider ON llm_logs(provider);
    CREATE INDEX idx_llm_logs_model ON llm_logs(model);
    CREATE INDEX idx_llm_logs_created_at ON llm_logs(created_at);
    CREATE INDEX idx_llm_logs_success ON llm_logs(success);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(migration_sql))
            conn.commit()
            print("✅ LLM logs table fixed successfully!")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("✅ Table recreated with correct schema!")
            print("")
            print("Next steps:")
            print("  1. Restart your backend server")
            print("  2. LLM logs page should now work correctly")
            return True
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Fixing LLM Logs Table...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    success = fix_tables()
    sys.exit(0 if success else 1)

