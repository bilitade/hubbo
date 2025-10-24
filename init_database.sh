#!/bin/bash

# Hubbo Database Initialization Script
# This script activates the virtual environment and initializes the database
#
# Usage:
#   ./init_database.sh                    - Initialize with default data
#   ./init_database.sh --with-sample-data - Initialize with sample data
#   ./init_database.sh --skip-drop        - Add to existing database without dropping tables

echo "========================================"
echo "Hubbo Database Initialization"
echo "========================================"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Initialize database with provided flags
echo "Initializing database..."
python -m app.scripts.init_database "$@"

echo ""
echo "========================================"
echo "Next steps:"
echo "1. Start backend:  uvicorn app.main:app --reload"
echo "2. Start frontend: npm run dev (in frontend directory)"
echo "3. Visit:          http://localhost:5173"
echo "4. Login with:     admin@example.com / Admin123!"
echo "========================================"
