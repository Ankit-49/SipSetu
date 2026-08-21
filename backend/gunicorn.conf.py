"""Gunicorn configuration for Flask-SocketIO with eventlet.

The eventlet worker requires monkey-patching BEFORE any other imports,
so this config file (loaded by gunicorn via ``-c gunicorn.conf.py``)
handles that.

Usage:
    gunicorn -c gunicorn.conf.py app:create_app()
"""

import eventlet
eventlet.monkey_patch()

# Worker config
worker_class = "eventlet"
workers = 1  # Eventlet worker must be single-process for SocketIO rooms
bind = "0.0.0.0:5000"
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
