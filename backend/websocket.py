"""Real-time WebSocket notifications (Phase 5.3).

Uses Flask-SocketIO with Redis message queue (gevent) for cross-process
pub/sub. Clients join a room named after their user_id and receive
events when notifications are created.

Falls back to a no-op when flask_socketio / eventlet / gevent are not
installed, so the rest of the app keeps working without WebSocket support.

Usage from routes or tasks:
    from websocket import emit_notification
    emit_notification(user_id, "New Match", "You matched a new job!", "success")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-init so imports never fail
_socketio = None
_initialized = False


def _detect_async_mode() -> str:
    """Detect the best available async mode for Flask-SocketIO."""
    try:
        import eventlet
        return "eventlet"
    except ImportError:
        pass
    try:
        import gevent
        return "gevent"
    except ImportError:
        pass
    return "threading"


def init_socketio(app=None):
    """Initialize Flask-SocketIO on an app (called once from app.py)."""
    global _socketio, _initialized
    if _initialized:
        return _socketio

    try:
        from flask_socketio import SocketIO

        redis_url = None
        if app:
            from config import settings
            redis_url = settings.REDIS_URL

        async_mode = _detect_async_mode()
        kwargs: dict[str, Any] = {
            "cors_allowed_origins": "*",
            "async_mode": async_mode,
        }
        if redis_url:
            kwargs["message_queue"] = redis_url

        _socketio = SocketIO(app, **kwargs)
        _initialized = True
        logger.info("Flask-SocketIO initialized")

        # Register event handlers
        @_socketio.on("connect")
        def handle_connect():
            logger.debug("WebSocket client connected")

        @_socketio.on("disconnect")
        def handle_disconnect():
            logger.debug("WebSocket client disconnected")

        @_socketio.on("join")
        def handle_join(data):
            """Client joins a room identified by user_id."""
            from flask import request as req
            user_id = data.get("user_id") if isinstance(data, dict) else data
            if user_id:
                _socketio.server.enter_room(req.sid, str(user_id))
                logger.debug(f"Client joined room: {user_id}")

        @_socketio.on("leave")
        def handle_leave(data):
            from flask import request as req
            user_id = data.get("user_id") if isinstance(data, dict) else data
            if user_id:
                _socketio.server.leave_room(req.sid, str(user_id))

    except ImportError:
        logger.info("Flask-SocketIO not installed; WebSocket notifications disabled")
        _initialized = True

    return _socketio


def emit_notification(user_id: str, title: str, message: str,
                      notif_type: str = "info",
                      related_job_id: str | None = None):
    """Push a real-time notification to a user's connected clients.

    Also used by tasks/ Celery workers via the Redis message queue so
    notifications arrive instantly even when emitted from a background
    worker process.
    """
    if not _socketio:
        return

    payload = {
        "title": title,
        "message": message,
        "type": notif_type,
        "related_job_id": related_job_id,
    }
    try:
        _socketio.emit("notification", payload, room=str(user_id))
    except Exception as e:
        logger.warning(f"WebSocket emit failed: {e}")


def emit_notification_count(user_id: str):
    """Push updated unread count to a user's connected clients."""
    if not _socketio:
        return

    try:
        from models import Notification
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        _socketio.emit("unread_count", {"count": count}, room=str(user_id))
    except Exception as e:
        logger.warning(f"WebSocket count emit failed: {e}")


def get_socketio():
    """Return the SocketIO instance (or None)."""
    return _socketio
