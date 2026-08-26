#!/bin/bash
# ========================================
# SipSetu - Local Backend Setup Script
# ========================================

set -e

echo ""
echo "========================================"
echo "  SipSetu - Local Backend Setup"
echo "========================================"
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "✓ Docker found: $(docker --version)"
    USE_DOCKER=true
else
    echo "⚠ Docker not found"
    echo "Will use local Python installation"
    USE_DOCKER=false
fi

# Check if Python is installed
if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    PYTHON_CMD=$(command -v python3 || command -v python)
    echo "✓ Python found: $($PYTHON_CMD --version)"
else
    if [ "$USE_DOCKER" = false ]; then
        echo "✗ Python not found! Please install Python 3.11+"
        exit 1
    fi
fi

echo ""

# Option 1: Docker deployment
if [ "$USE_DOCKER" = true ]; then
    echo "Docker detected. Starting services with Docker Compose..."
    echo ""
    
    # Copy environment file if not exists
    if [ ! -f ".env.production" ]; then
        echo "Creating .env.production..."
        cp .env.production.example .env.production
        
        # Generate random passwords
        POSTGRES_PASSWORD=$(openssl rand -base64 32)
        REDIS_PASSWORD=$(openssl rand -base64 32)
        JWT_SECRET_KEY=$(openssl rand -hex 32)
        
        # Update .env.production
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env.production 2>/dev/null || \
        sed -i '' "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env.production
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env.production 2>/dev/null || \
        sed -i '' "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env.production
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env.production 2>/dev/null || \
        sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env.production
        
        echo "✓ .env.production created with random passwords"
    fi
    
    echo "Starting Docker services..."
    docker compose -f docker-compose.prod.yml up -d postgres redis backend celery-worker celery-beat
    
    echo ""
    echo "Waiting for services to start..."
    sleep 15
    
    echo ""
    echo "Checking service status..."
    docker compose -f docker-compose.prod.yml ps
    
    echo ""
    echo "✓ Backend started on http://localhost:5000"
    
# Option 2: Local Python deployment
else
    echo "Starting local Python deployment..."
    echo ""
    
    cd backend
    
    # Create virtual environment if not exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate 2>/dev/null || venv\Scripts\activate
    
    echo "✓ Virtual environment activated"
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    echo "✓ Dependencies installed"
    
    # Check for PostgreSQL and Redis
    echo ""
    echo "⚠ Make sure PostgreSQL and Redis are running:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    
    # Run migrations
    echo "Running database migrations..."
    python -m alembic upgrade head
    
    echo "✓ Migrations completed"
    
    # Start backend
    echo ""
    echo "Starting backend server..."
    python app.py &
    
    echo ""
    echo "✓ Backend started on http://localhost:5000"
fi

echo ""
echo "========================================"
echo "  Backend Setup Complete!"
echo "========================================"
echo ""
echo "Backend URL: http://localhost:5000"
echo "Health Check: http://localhost:5000/api/health"
echo ""
echo "Next steps:"
echo "1. Deploy frontend to Cloudflare Pages"
echo "2. Set VITE_API_URL to http://localhost:5000/api"
echo "3. Or use ngrok to expose backend: ngrok http 5000"
echo ""
