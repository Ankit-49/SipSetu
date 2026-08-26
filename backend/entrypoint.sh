#!/bin/bash
set -e

# Graceful shutdown handler
shutdown_handler() {
    echo "Received shutdown signal, gracefully stopping..."
    # Kill the gunicorn process
    if [ -n "$GUNICORN_PID" ]; then
        kill -TERM "$GUNICORN_PID" 2>/dev/null
        wait "$GUNICORN_PID"
    fi
    echo "Shutdown complete"
    exit 0
}

# Trap SIGTERM and SIGINT for graceful shutdown
trap shutdown_handler SIGTERM SIGINT

# Wait for database to be ready
echo "Waiting for database..."
python -c "
import time
import os
import psycopg2
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    parsed = urlparse(db_url)
    max_retries = 30
    retry_count = 0
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                dbname=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
            conn.close()
            print('Database is ready!')
            break
        except psycopg2.OperationalError:
            retry_count += 1
            print(f'Database not ready, retrying ({retry_count}/{max_retries})...')
            time.sleep(2)
    else:
        print('Database connection failed after max retries')
        exit 1
else:
    print('No DATABASE_URL configured, skipping database check')
"

# Run Alembic migrations if ENABLE_MIGRATIONS is set
if [ "$ENABLE_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || echo "Migration warning (non-fatal)"
fi

# Start gunicorn with graceful shutdown
echo "Starting gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers ${GUNICORN_WORKERS:-4} \
    --worker-class gevent \
    --worker-connections ${GUNICORN_WORKER_CONNECTIONS:-1000} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT:-30} \
    --keep-alive ${GUNICORN_KEEP_ALIVE:-5} \
    --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
    --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-50} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --preload \
    app:create_app() &

# Store gunicorn PID
GUNICORN_PID=$!

# Wait for gunicorn to start
sleep 2

# Keep script running and wait for gunicorn
wait $GUNICORN_PID
