#!/bin/bash

# HUBBO Backend Setup Script
# Quick setup for development and production environments

set -e

echo "=========================================="
echo "🚀 HUBBO Backend - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    print_error "app/main.py not found. Run this script from project root."
    exit 1
fi

# Parse command line arguments
SKIP_VENV=false
SKIP_DB=false
PRODUCTION=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --skip-db)
            SKIP_DB=true
            shift
            ;;
        --production)
            PRODUCTION=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./setup.sh [--skip-venv] [--skip-db] [--production]"
            exit 1
            ;;
    esac
done

# Step 1: Virtual Environment
if [ "$SKIP_VENV" = false ]; then
    echo "📦 Setting up virtual environment..."
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    print_info "Activating virtual environment..."
    source .venv/bin/activate
    
    print_info "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
    echo ""
fi

# Step 2: Environment Configuration
echo "🔐 Configuring environment..."
if [ "$PRODUCTION" = true ]; then
    if [ ! -f ".env.production" ]; then
        print_warning ".env.production not found"
        if [ -f ".env.example" ]; then
            cp .env.example .env.production
            print_info "Created .env.production from .env.example"
            print_warning "IMPORTANT: Edit .env.production with production values!"
        fi
    else
        print_success ".env.production exists"
    fi
else
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created from template"
            print_warning "Edit .env file with your configuration"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_success ".env file exists"
    fi
fi
echo ""

# Step 3: Database Setup
if [ "$SKIP_DB" = false ]; then
    echo "🗄️  Database setup..."
    read -p "Initialize database with sample data? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Initializing database..."
        python3 -m app.scripts.init_database
        print_success "Database initialized with sample data"
    fi
    echo ""
fi

# Step 4: Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/uploads data/vectorstore logs
print_success "Directories created"
echo ""

# Final instructions
echo "=========================================="
print_success "Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next steps:"
echo ""
if [ "$PRODUCTION" = true ]; then
    echo "1. Edit .env.production with your production values:"
    echo "   ${YELLOW}nano .env.production${NC}"
    echo ""
    echo "2. Deploy with Docker:"
    echo "   ${YELLOW}docker-compose up -d${NC}"
    echo ""
    echo "3. Check health:"
    echo "   ${YELLOW}curl http://localhost:8000/health${NC}"
else
    echo "1. Activate virtual environment:"
    echo "   ${YELLOW}source .venv/bin/activate${NC}"
    echo ""
    echo "2. Start development server:"
    echo "   ${YELLOW}uvicorn app.main:app --reload${NC}"
    echo ""
    echo "3. Access the API:"
    echo "   • Swagger UI: ${BLUE}http://localhost:8000/docs${NC}"
    echo "   • ReDoc: ${BLUE}http://localhost:8000/redoc${NC}"
    echo "   • Health: ${BLUE}http://localhost:8000/health${NC}"
    echo ""
    echo "4. Default credentials:"
    echo "   • Email: ${YELLOW}admin@example.com${NC}"
    echo "   • Password: ${YELLOW}Admin123!${NC}"
fi
echo ""
echo "=========================================="
