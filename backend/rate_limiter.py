"""
Simple in-memory rate limiter for Flask routes.

Uses a process-local dict keyed by ``{endpoint}:{identifier}`` with lists of
request timestamps.  Works correctly under the Flask dev server (single-process)
but must be replaced with a Redis-backed limiter for multi-worker production.

Usage
-----
from rate_limiter import rate_limit

@api.route("/auth/verify-email", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=600, key_by="email")
def verify_email():
    ...
"""

from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from flask import jsonify, request

# _rate_store[store_key] = [timestamp, ...]
_rate_store: dict[str, list[float]] = defaultdict(list)


def rate_limit(
    max_requests: int,
    window_seconds: int,
    key_by: str | Callable[[], str] | None = None,
) -> Callable:
    """Decorate a Flask route to enforce a maximum request rate.

    Parameters
    ----------
    max_requests : int
        Maximum number of requests allowed within *window_seconds*.
    window_seconds : int
        Width of the sliding window in seconds.
    key_by : str | callable | None
        How to derive the per-request identifier that is appended to the
        endpoint name to form the store key.  Built-in options:

        - ``"ip"``        — ``request.remote_addr`` (default)
        - ``"email"``     — ``(request.get_json() or {}).get("email", "")``
        - ``"user_id"``   — ``g.current_user_id`` (must be set by auth middleware)

        A callable can be passed for custom logic (must return a string).
        If ``None`` (or omitted) the client IP is used.

    Returns
    -------
    Decorated function that returns ``429 Too Many Requests`` when the
    limit is exceeded.
    """
    if isinstance(key_by, str):
        _resolver = _BUILTIN_KEY_RESOLVERS.get(key_by)
        if _resolver is None:
            raise ValueError(f"Unknown key_by '{key_by}'.  Use 'ip', 'email', 'user_id', or pass a callable.")
    elif callable(key_by):
        _resolver = key_by
    else:
        _resolver = _BUILTIN_KEY_RESOLVERS["ip"]

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key_part = _resolver()
            store_key = f"{request.endpoint}:{key_part}"

            now = time.time()
            cutoff = now - window_seconds

            timestamps = _rate_store[store_key]
            # Retain only entries still within the window
            timestamps = [t for t in timestamps if t > cutoff]

            if len(timestamps) >= max_requests:
                retry_after = int(timestamps[0] + window_seconds - now)
                return jsonify({
                    "error": f"Too many requests. Please try again in {retry_after} seconds.",
                }), 429

            timestamps.append(now)
            _rate_store[store_key] = timestamps

            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Built-in key resolvers
# ---------------------------------------------------------------------------

def _key_by_ip() -> str:
    return request.remote_addr or "unknown"


def _key_by_email() -> str:
    data = request.get_json(silent=True) or {}
    return (data.get("email") or "").strip().lower() or "no-email"


def _key_by_user_id() -> str:
    # Import here to avoid circular import at module load time
    from flask import g

    return str(getattr(g, "current_user_id", "anonymous"))


_BUILTIN_KEY_RESOLVERS: dict[str, Callable[[], str]] = {
    "ip": _key_by_ip,
    "email": _key_by_email,
    "user_id": _key_by_user_id,
}
