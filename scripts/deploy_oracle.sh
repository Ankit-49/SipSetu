#!/bin/bash
# ========================================
# SipSetu - Oracle Cloud Deployment Script
# ========================================

set -e

echo ""
echo "========================================"
echo "  SipSetu - Oracle Cloud Deployment"
echo "========================================"
echo ""

# Check if running on Oracle Cloud
if curl -s --connect-timeout 2 http://169.254.169.254/opc/v1/instance/ > /dev/null 2>&1; then
    echo "✓ Running on Oracle Cloud"
else
    echo "⚠ Not running on Oracle Cloud (or metadata service unavailable)"
fi
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✓ Docker installed"
    echo "⚠ Please log out and back in, or run: newgrp docker"
    exit 1
fi

echo "✓ Docker found: $(docker --version)"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "Docker Compose not found. Installing..."
    sudo apt install docker-compose-plugin -y
fi

echo "✓ Docker Compose found"
echo ""

# Check if SipSetu is cloned
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "SipSetu not found. Cloning..."
    git clone https://github.com/Ankit-49/SipSetu.git
    cd SipSetu
fi

echo "✓ SipSetu found"
echo ""

# Create .env.production if not exists
if [ ! -f ".env.production" ]; then
    echo "Creating .env.production..."
    cp .env.production.example .env.production
    
    # Generate random passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    
    # Get public IP
    PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "localhost")
    
    # Update .env.production
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env.production
    sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env.production
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env.production
    sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=http://$PUBLIC_IP|" .env.production
    
    echo "✓ .env.production created"
    echo ""
    echo "Important: Your public IP is: $PUBLIC_IP"
    echo "Access SipSetu at: http://$PUBLIC_IP"
    echo ""
fi

echo ""
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build

echo ""
echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "Waiting for services to start..."
sleep 10

echo ""
echo "Checking service status..."
docker compose -f docker-compose.prod.yml ps

echo ""
echo "========================================"
echo "  Deployment Complete!"
echo "========================================"
echo ""

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me || curl -s icanhazip.com || echo "localhost")
echo "Frontend URL: http://$PUBLIC_IP"
echo "Backend Health: http://$PUBLIC_IP:5000/api/health"
echo ""

echo "Useful commands:"
echo "  docker compose -f docker-compose.prod.yml logs -f          # View logs"
echo "  docker compose -f docker-compose.prod.yml ps               # Check status"
echo "  docker compose -f docker-compose.prod.yml restart backend  # Restart backend"
echo "  docker compose -f docker-compose.prod.yml down             # Stop all"
echo ""
