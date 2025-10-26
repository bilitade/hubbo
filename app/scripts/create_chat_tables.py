"""Create chat tables for AI assistant."""
from sqlalchemy import text
from app.db.session import engine
from app.models import Chat, ChatThread, ChatMessage


def create_chat_tables():
    """Create chat tables."""
    with engine.begin() as conn:
        # Create chats table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chats (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title TEXT NOT NULL,
                description TEXT,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                is_archived BOOLEAN DEFAULT FALSE NOT NULL,
                is_pinned BOOLEAN DEFAULT FALSE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                last_message_at TIMESTAMP WITH TIME ZONE
            );
        """))
        
        # Create chat_threads table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_threads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                title TEXT,
                context JSONB,
                system_prompt TEXT,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                message_count INTEGER DEFAULT 0 NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """))
        
        # Create chat_messages table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                thread_id UUID NOT NULL REFERENCES chat_threads(id) ON DELETE CASCADE,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                extra_data JSONB,
                model VARCHAR(100),
                tokens_used INTEGER,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CHECK (role IN ('user', 'assistant', 'system'))
            );
        """))
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);
            CREATE INDEX IF NOT EXISTS idx_chats_updated_at ON chats(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_chat_threads_chat_id ON chat_threads(chat_id);
            CREATE INDEX IF NOT EXISTS idx_chat_threads_updated_at ON chat_threads(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_id ON chat_messages(thread_id);
            CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at ASC);
        """))
        
        print("✅ Chat tables created successfully!")


def main():
    """Main function."""
    try:
        create_chat_tables()
    except Exception as e:
        print(f"❌ Error creating chat tables: {e}")
        raise


if __name__ == "__main__":
    main()

