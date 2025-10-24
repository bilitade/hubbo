#!/bin/bash

# Hubbo Database Initialization Script
# This script activates the virtual environment and initializes the database

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

# Check if --with-sample-data flag is provided
if [ "$1" == "--with-sample-data" ]; then
    echo "Initializing database with sample data..."
    python -m app.scripts.init_hubbo_db --with-sample-data
else
    echo "Initializing database..."
    python -m app.scripts.init_hubbo_db
fi

echo ""
echo "========================================"
echo "Next steps:"
echo "1. Start the server: uvicorn app.main:app --reload"
echo "2. Access API docs: http://localhost:8000/docs"
echo "3. Login with: admin@example.com / Admin123!"
echo "========================================"
