#!/bin/bash

# Run System Settings Migration
# This script creates the system_settings table in the database

echo "🚀 Running System Settings Migration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running. Please start it first."
    exit 1
fi

# Run the migration
psql -U postgres -d hubbo -f migrations/002_create_system_settings.sql

if [ $? -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ Migration completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Restart your backend server"
    echo "  2. Navigate to Settings page in the frontend"
    echo "  3. Configure your AI keys and email settings"
    echo ""
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Migration failed. Check the errors above."
    exit 1
fi

