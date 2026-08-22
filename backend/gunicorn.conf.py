"""Gunicorn configuration for Flask-SocketIO.

For production with SocketIO support, use:
    gunicorn -c gunicorn.conf.py app:create_app()

For simple deployments without SocketIO, the Dockerfile uses inline flags.
"""

# Worker config
worker_class = "gevent"
workers = 4
bind = "0.0.0.0:5000"
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
