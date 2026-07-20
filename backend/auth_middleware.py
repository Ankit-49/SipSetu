"""JWT authentication and role-based access control middleware."""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def create_token(user_id: str, role: str) -> str:
    """Generate a JWT access token for the given user."""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow()
        + timedelta(hours=current_app.config["JWT_EXPIRATION_HOURS"]),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
    )


def extract_token() -> str | None:
    """Extract Bearer token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def require_auth(f):
    """Decorator that enforces a valid JWT token on the endpoint.

    On success, sets ``g.current_user_id`` and ``g.current_user_role``
    for downstream use.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token()
        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            payload = decode_token(token)
            g.current_user_id = payload["user_id"]
            g.current_user_role = payload["role"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


def require_role(*roles: str):
    """Decorator that enforces both JWT auth AND a specific user role.

    Usage::

        @api.route('/jobs', methods=['POST'])
        @require_role('recruiter')
        def create_job():
            ...
    """

    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            if g.current_user_role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)

        return decorated

    return decorator
