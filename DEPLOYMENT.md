# SipSetu Deployment Guide

This guide covers deploying SipSetu to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Configuration](#configuration)
6. [Database Migrations](#database-migrations)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 20GB+ available space
- **OS**: Ubuntu 20.04+, Debian 11+, or similar Linux distribution

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git

### For Manual Deployment

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

---

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Ankit-49/SipSetu.git
cd SipSetu
```

### 2. Create Environment File

```bash
cp .env.production.example .env.production
```

### 3. Configure Environment Variables

Edit `.env.production` with your production values:

```bash
# Required - Generate strong secrets
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Required - Email configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# Required - Domain configuration
FRONTEND_URL=https://yourdomain.com

# Required - Admin access
ADMIN_EMAILS=admin@yourdomain.com
```

---

## Docker Deployment

### Quick Start

```bash
# Build and start all services
make prod-d

# Or manually
docker compose -f docker-compose.prod.yml up -d
```

### Step-by-Step Deployment

#### 1. Build Docker Images

```bash
# Build backend
make build-backend-prod

# Build frontend
make build-frontend
```

#### 2. Start Infrastructure Services

```bash
# Start database and cache
docker compose -f docker-compose.prod.yml up -d postgres redis
```

#### 3. Run Database Migrations

```bash
# Enable migrations and restart backend
ENABLE_MIGRATIONS=true docker compose -f docker-compose.prod.yml up -d backend

# Or run manually
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

#### 4. Start Application Services

```bash
# Start all services
docker compose -f docker-compose.prod.yml up -d

# Start with monitoring
docker compose -f docker-compose.prod.yml --profile observability up -d
```

#### 5. Verify Deployment

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# Run health check
python backend/scripts/health_check.py --url http://localhost:5000

# View logs
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## Manual Deployment

### Backend Setup

#### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/sipsetu
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=your-secret-key
# ... other environment variables
```

#### 3. Run Migrations

```bash
python -m alembic upgrade head
```

#### 4. Start Application

```bash
# Development
python app.py

# Production (with gunicorn)
gunicorn -k gevent -w 4 -b 0.0.0.0:5000 app:create_app()
```

### Frontend Setup

#### 1. Install Dependencies

```bash
cd frontend
npm install
```

#### 2. Build for Production

```bash
npm run build
```

#### 3. Serve with Nginx

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
    }
}
```

---

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `POSTGRES_DB` | Database name | Yes | `sipsetu` |
| `POSTGRES_USER` | Database user | Yes | `postgres` |
| `POSTGRES_PASSWORD` | Database password | Yes | - |
| `REDIS_PASSWORD` | Redis password | Yes | - |
| `JWT_SECRET_KEY` | JWT signing key | Yes | - |
| `FRONTEND_URL` | Frontend URL | Yes | - |
| `SMTP_HOST` | SMTP server | Yes | - |
| `SMTP_PORT` | SMTP port | Yes | `587` |
| `SMTP_USER` | SMTP username | Yes | - |
| `SMTP_PASSWORD` | SMTP password | Yes | - |
| `ADMIN_EMAILS` | Admin emails (comma-separated) | Yes | - |
| `SENTRY_DSN` | Sentry DSN | No | - |
| `OTEL_ENABLED` | Enable OpenTelemetry | No | `false` |
| `ENABLE_MIGRATIONS` | Run migrations on startup | No | `false` |
| `LOG_LEVEL` | Log level | No | `info` |

### SSL/TLS Configuration

For HTTPS, you'll need to:

1. Obtain SSL certificates (Let's Encrypt recommended)
2. Configure nginx with SSL settings
3. Update `FRONTEND_URL` to use HTTPS

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## Database Migrations

### Running Migrations

```bash
# Via Docker
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head

# Via Make
make migrate

# Manually
cd backend
python -m alembic upgrade head
```

### Creating New Migrations

```bash
# Via Make
make migrate-create name="add_new_feature"

# Manually
cd backend
python -m alembic revision --autogenerate -m "add_new_feature"
```

### Rollback

```bash
# Rollback one step
python -m alembic downgrade -1

# Rollback to specific version
python -m alembic downgrade <revision_id>
```

---

## Monitoring

### Prometheus

- **URL**: http://localhost:9090
- **Metrics**: http://localhost:5000/metrics

### Grafana

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: Set in `GRAFANA_ADMIN_PASSWORD`

### Flower (Celery)

- **URL**: http://localhost:5555
- **Username**: admin
- **Password**: Set in `FLOWER_BASIC_AUTH`

### Loki (Logs)

- **URL**: http://localhost:3100
- **Logs**: Viewable in Grafana

### Health Check

```bash
# Run comprehensive health check
python backend/scripts/health_check.py --url http://localhost:5000 --verbose

# Simple health check
curl http://localhost:5000/api/health
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check if PostgreSQL is running
docker compose -f docker-compose.prod.yml ps postgres

# Check logs
docker compose -f docker-compose.prod.yml logs postgres

# Test connection
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres -d sipsetu
```

#### 2. Redis Connection Failed

```bash
# Check if Redis is running
docker compose -f docker-compose.prod.yml ps redis

# Test connection
docker compose -f docker-compose.prod.yml exec redis redis-cli -a your-password ping
```

#### 3. Backend Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Common issues:
# - Missing environment variables
# - Database not ready
# - Port already in use
```

#### 4. Frontend Build Failed

```bash
# Clear cache and rebuild
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

#### 5. Migration Errors

```bash
# Check current migration state
docker compose -f docker-compose.prod.yml exec backend python -m alembic current

# If stuck, stamp to specific version
docker compose -f docker-compose.prod.yml exec backend python -m alembic stamp head
```

### Performance Tuning

#### Gunicorn Workers

```bash
# Default: 4 workers
# Recommended: 2 * CPU cores + 1
GUNICORN_WORKERS=9  # For 4-core CPU
```

#### Database Connection Pool

```bash
# In config.py or environment
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

#### Redis Memory

```bash
# Monitor Redis memory
docker compose -f docker-compose.prod.yml exec redis redis-cli info memory
```

### Backup & Recovery

#### Database Backup

```bash
# Backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres sipsetu > backup.sql

# Restore
docker compose -f docker-compose.prod.yml exec postgres psql -U postgres sipsetu < backup.sql
```

#### Redis Backup

```bash
# Backup
docker compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE

# Copy dump.rdb file
docker cp sipsetu-redis:/data/dump.rdb ./redis-backup.rdb
```

### Logs

```bash
# View all logs
docker compose -f docker-compose.prod.yml logs -f

# View specific service
docker compose -f docker-compose.prod.yml logs -f backend

# View last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

---

## Security Best Practices

1. **Use strong passwords** for all services
2. **Enable HTTPS** in production
3. **Restrict access** to monitoring endpoints
4. **Regular backups** of database and Redis
5. **Monitor logs** for suspicious activity
6. **Keep dependencies updated**
7. **Use environment variables** for secrets (not hardcoded)
8. **Enable rate limiting** to prevent abuse
9. **Review security headers** (CSP, HSTS, etc.)

---

## Support

- **Documentation**: Check this guide and README.md
- **Issues**: https://github.com/Ankit-49/SipSetu/issues
- **Discussions**: https://github.com/Ankit-49/SipSetu/discussions
