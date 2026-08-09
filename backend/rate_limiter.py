"""
Redis-backed rate limiter with in-memory fallback.

Supports both single-process development (in-memory) and multi-worker production (Redis).
"""

from __future__ import annotations

import time
import os
from collections import defaultdict
from functools import wraps
from typing import Callable, Optional

from flask import jsonify, request, current_app, g

# Try to import Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_FLASK_LIMITER = True
except ImportError:
    HAS_FLASK_LIMITER = False


# In-memory store (fallback for development)
_rate_store: dict[str, list[float]] = defaultdict(list)


class RateLimiter:
    """Unified rate limiter supporting both Redis and in-memory backends."""
    
    def __init__(self, app=None):
        self.app = app
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        self.flask_limiter: Optional[Limiter] = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.app = app
        redis_url = os.environ.get('REDIS_URL')
        
        # Try Flask-Limiter with Redis first
        if HAS_FLASK_LIMITER and HAS_REDIS and redis_url:
            try:
                self.flask_limiter = Limiter(
                    app=app,
                    key_func=get_remote_address,
                    storage_uri=redis_url,
                    default_limits=["200 per minute", "50 per second"],
                    storage_options={"socket_connect_timeout": 3, "socket_timeout": 3},
                    strategy="sliding-window",
                )
                self.use_redis = True
                app.logger.info("Using Redis-backed rate limiter (flask-limiter)")
                return
            except Exception as e:
                app.logger.warning(f"Flask-Limiter init failed, trying raw Redis: {e}")
        
        # Try raw Redis client
        if HAS_REDIS and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.use_redis = True
                app.logger.info("Using Redis-backed rate limiter (raw redis-py)")
                return
            except Exception as e:
                app.logger.warning(f"Raw Redis init failed: {e}")
        
        # Fall back to in-memory
        app.logger.warning("Using in-memory rate limiter (not suitable for multi-worker production)")
        self.use_redis = False
    
    def limit(self, max_requests: int, window_seconds: int, key_by: str | Callable[[], str] | None = None):
        """Decorator for rate limiting a route."""
        if self.use_redis and self.flask_limiter:
            # Use Flask-Limiter's decorator
            return self.flask_limiter.limit(f"{max_requests} per {window_seconds} seconds")
        
        if self.use_redis and self.redis_client:
            # Use raw Redis with sliding window
            return self._redis_limit(max_requests, window_seconds, key_by)
        
        # Fall back to in-memory
        return self._memory_limit(max_requests, window_seconds, key_by)
    
    def _redis_limit(self, max_requests: int, window_seconds: int, key_by: str | Callable[[], str] | None):
        """Redis-backed sliding window rate limiter using sorted sets."""
        if isinstance(key_by, str):
            resolver = _BUILTIN_KEY_RESOLVERS.get(key_by)
            if resolver is None:
                raise ValueError(f"Unknown key_by '{key_by}'")
        elif callable(key_by):
            resolver = key_by
        else:
            resolver = _BUILTIN_KEY_RESOLVERS["ip"]
        
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                key_part = resolver()
                store_key = f"ratelimit:{request.endpoint}:{key_part}"
                
                now = time.time()
                window_start = now - window_seconds
                
                pipe = self.redis_client.pipeline()
                # Remove expired entries
                pipe.zremrangebyscore(store_key, 0, window_start)
                # Count current requests
                pipe.zcard(store_key)
                results = pipe.execute()
                
                current_count = results[1]
                
                if current_count >= max_requests:
                    # Get oldest entry to calculate retry-after
                    oldest = self.redis_client.zrange(store_key, 0, 0, withscores=True)
                    if oldest:
                        retry_after = int(oldest[0][1] + window_seconds - now) + 1
                    else:
                        retry_after = window_seconds
                    
                    return jsonify({
                        "error": f"Too many requests. Please try again in {retry_after} seconds.",
                    }), 429
                
                # Add current request
                self.redis_client.zadd(store_key, {f"{now}:{os.urandom(4).hex()}": now})
                self.redis_client.expire(store_key, window_seconds + 1)
                
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    def _memory_limit(self, max_requests: int, window_seconds: int, key_by: str | Callable[[], str] | None):
        """In-memory sliding window rate limiter (original implementation)."""
        if isinstance(key_by, str):
            resolver = _BUILTIN_KEY_RESOLVERS.get(key_by)
            if resolver is None:
                raise ValueError(f"Unknown key_by '{key_by}'")
        elif callable(key_by):
            resolver = key_by
        else:
            resolver = _BUILTIN_KEY_RESOLVERS["ip"]
        
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                key_part = resolver()
                store_key = f"{request.endpoint}:{key_part}"
                
                now = time.time()
                cutoff = now - window_seconds
                
                timestamps = _rate_store[store_key]
                timestamps = [t for t in timestamps if t > cutoff]
                
                if len(timestamps) >= max_requests:
                    retry_after = int(timestamps[0] + window_seconds - now) + 1
                    return jsonify({
                        "error": f"Too many requests. Please try again in {retry_after} seconds.",
                    }), 429
                
                timestamps.append(now)
                _rate_store[store_key] = timestamps
                
                return f(*args, **kwargs)
            return wrapper
        return decorator


# Built-in key resolvers
def _key_by_ip() -> str:
    return request.remote_addr or "unknown"


def _key_by_email() -> str:
    data = request.get_json(silent=True) or {}
    return (data.get("email") or "").strip().lower() or "no-email"


def _key_by_user_id() -> str:
    from flask import g
    return str(getattr(g, "current_user_id", "anonymous"))


_BUILTIN_KEY_RESOLVERS: dict[str, Callable[[], str]] = {
    "ip": _key_by_ip,
    "email": _key_by_email,
    "user_id": _key_by_user_id,
}


# Global instance for backward compatibility
_limiter_instance: Optional[RateLimiter] = None


def get_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = RateLimiter()
        if current_app:
            _limiter_instance.init_app(current_app)
    return _limiter_instance


def rate_limit(
    max_requests: int,
    window_seconds: int,
    key_by: str | Callable[[], str] | None = None,
) -> Callable:
    """Decorator for rate limiting (backward compatible with old API)."""
    limiter = get_limiter()
    return limiter.limit(max_requests, window_seconds, key_by)


# For direct use in routes that need the limiter instance
def init_rate_limiter(app):
    """Initialize rate limiter with Flask app."""
    global _limiter_instance
    _limiter_instance = RateLimiter(app)
    return _limiter_instance