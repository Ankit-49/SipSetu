"""Gunicorn configuration for Flask-SocketIO.

For production with SocketIO support, use:
    gunicorn -c gunicorn.conf.py --preload app:create_app()

For simple deployments without SocketIO, the Dockerfile uses inline flags.
"""

import os
import multiprocessing

# Worker config
worker_class = "gevent"
workers = int(os.getenv("GUNICORN_WORKERS", min(2, multiprocessing.cpu_count())))
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5000")
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
