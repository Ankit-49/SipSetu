# Backend Dockerfile - Multi-stage build
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with home set to /app
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
ENV HOME=/app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create ml_artifacts directory and set permissions
RUN mkdir -p ml_artifacts && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# Health check — start-period raised so ML imports finish before first probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health', timeout=5)" || exit 1

# --preload loads the app once in the master (saves ~70 % RAM vs per-worker)
# -w 2 keeps us well under the Render free-tier 512 MB limit
CMD ["gunicorn", "-c", "gunicorn.conf.py", "--preload", "-w", "2", "-b", "0.0.0.0:5000", "app:create_app()"]
