#!/bin/bash
# HUBBO Docker Startup Script

set -e

echo "🚀 Starting HUBBO with Docker..."
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Creating .env from template..."
    cp env.template .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and update:"
    echo "  - DB_PASSWORD"
    echo "  - SECRET_KEY"
    echo "  - Email credentials"
    echo "  - AI API keys (if using AI features)"
    echo ""
    read -p "Press Enter to continue after editing .env..."
fi

# Build and start containers
echo ""
echo "🏗️  Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if backend is healthy
echo ""
echo "🔍 Checking backend health..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ Backend is healthy!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend health check failed!"
    echo "Showing logs:"
    docker-compose logs backend
    exit 1
fi

echo ""
echo "================================"
echo "🎉 HUBBO is running!"
echo "================================"
echo ""
echo "📍 Services:"
echo "  Backend API: http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Health:      http://localhost:8000/health"
echo ""
echo "📝 Default Login:"
echo "  Email:    admin@example.com"
echo "  Password: Admin123!"
echo ""
echo "🔧 Useful Commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop:          docker-compose stop"
echo "  Restart:       docker-compose restart"
echo "  Shell access:  docker-compose exec backend bash"
echo "  Run migration: docker-compose exec backend python migrate.py"
echo "  Seed data:     docker-compose exec backend python seed.py"
echo ""
echo "================================"

