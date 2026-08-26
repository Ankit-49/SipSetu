.PHONY: help dev prod test lint build clean

# Default target
help:
	@echo "SipSetu - Available Commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make prod         - Start production environment"
	@echo "  make test         - Run all tests"
	@echo "  make test-backend - Run backend tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make test-e2e     - Run E2E tests"
	@echo "  make lint         - Run linting"
	@echo "  make lint-backend - Run backend linting"
	@echo "  make lint-frontend - Run frontend linting"
	@echo "  make build        - Build all Docker images"
	@echo "  make build-backend - Build backend Docker image"
	@echo "  make build-frontend - Build frontend Docker image"
	@echo "  make clean        - Clean up containers and volumes"
	@echo "  make logs         - View logs from all services"
	@echo "  make logs-backend - View backend logs"
	@echo "  make migrate      - Run database migrations"
	@echo "  make seed         - Seed database with test data"

# Development
dev:
	docker compose up

dev-d:
	docker compose up -d

# Production
prod:
	docker compose -f docker-compose.prod.yml up

prod-d:
	docker compose -f docker-compose.prod.yml up -d

# Testing
test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -v --tb=short

test-frontend:
	cd frontend && npm test

test-e2e:
	npx playwright test

# Linting
lint: lint-backend lint-frontend

lint-backend:
	cd backend && python -m ruff check .
	cd backend && python -m mypy . --ignore-missing-imports

lint-frontend:
	cd frontend && npm run lint
	cd frontend && npm run typecheck

# Building
build: build-backend build-frontend

build-backend:
	docker build -t sipsetu-backend:latest -f backend/Dockerfile backend

build-backend-prod:
	docker build -t sipsetu-backend:prod -f backend/Dockerfile.prod backend

build-frontend:
	docker build -t sipsetu-frontend:latest frontend

# Cleanup
clean:
	docker compose down -v
	docker compose -f docker-compose.prod.yml down -v
	docker system prune -f

# Logs
logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

# Database
migrate:
	docker compose exec backend python -m alembic upgrade head

migrate-create:
	docker compose exec backend python -m alembic revision --autogenerate -m "$(name)"

seed:
	docker compose exec backend python scripts/seed_data.py

# Utility
shell-backend:
	docker compose exec backend bash

shell-postgres:
	docker compose exec postgres psql -U postgres -d sipsetu

redis-cli:
	docker compose exec redis redis-cli

# Monitoring
monitoring:
	docker compose --profile observability up

monitoring-d:
	docker compose --profile observability up -d
