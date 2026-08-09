import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from config import settings, Config

load_dotenv()

# Optional imports for production features
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    HAS_LIMITER = True
except ImportError:
    HAS_LIMITER = False

try:
    from flask_talisman import Talisman
    HAS_TALISMAN = True
except ImportError:
    HAS_TALISMAN = False

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

# Logging
from logging_config import setup_logging, log_request_middleware


def create_app():
    app = Flask(__name__)
    
    # Configure logging first
    setup_logging(app)
    log_request_middleware(app)
    
    # Configure CORS with explicit origins
    frontend_url = settings.FRONTEND_URL
    CORS(app, origins=[frontend_url], supports_credentials=True)

    app.config.from_object(Config)

    # Database configuration
    db_url = settings.DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': settings.DB_POOL_RECYCLE,
        'pool_size': settings.DB_POOL_SIZE,
        'max_overflow': settings.DB_MAX_OVERFLOW,
    }

    db.init_app(app)

    # Security headers with Talisman (production only)
    if HAS_TALISMAN and not app.debug and settings.ENVIRONMENT == 'production':
        csp = {
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'", "https:", "data:"],
            'connect-src': ["'self'", frontend_url],
        }
        Talisman(
            app,
            content_security_policy=csp,
            force_https=True,
            strict_transport_security=True,
            session_cookie_secure=True,
            referrer_policy='strict-origin-when-cross-origin',
        )

    # Redis-backed rate limiter
    limiter = None
    if HAS_LIMITER and HAS_REDIS:
        redis_url = settings.REDIS_URL
        if redis_url:
            try:
                limiter = Limiter(
                    app=app,
                    key_func=get_remote_address,
                    storage_uri=redis_url,
                    default_limits=[settings.RATE_LIMIT_DEFAULT],
                    storage_options={"socket_connect_timeout": 3, "socket_timeout": 3},
                    strategy="sliding-window",
                )
                app.limiter = limiter
            except Exception as e:
                app.logger.warning(f"Failed to initialize Redis rate limiter: {e}")
                from rate_limiter import rate_limit as fallback_rate_limit
                app.fallback_rate_limit = fallback_rate_limit

    # Register routes
    from routes import api
    app.register_blueprint(api, url_prefix='/api')

    # Initialize database and run migrations
    with app.app_context():
        db.create_all()
        # Safe migration check for columns added after initial schema
        try:
            db.session.execute(db.text("ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending' NOT NULL"))
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT"))
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE"))
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)"))
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
            db.session.execute(db.text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS reminders_sent VARCHAR(255) DEFAULT ''"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Migration warning: {e}")

    # Health check with dependency verification
    @app.route('/api/health', methods=['GET'])
    def health_check():
        health = {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "checks": {}
        }
        
        # Database check
        try:
            db.session.execute(db.text("SELECT 1"))
            health["checks"]["database"] = "ok"
        except Exception as e:
            health["checks"]["database"] = f"failed: {str(e)[:100]}"
            health["status"] = "degraded"
        
        # Redis check (if configured)
        redis_url = settings.REDIS_URL
        if redis_url and HAS_REDIS:
            try:
                r = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                r.ping()
                health["checks"]["redis"] = "ok"
            except Exception as e:
                health["checks"]["redis"] = f"failed: {str(e)[:100]}"
                health["status"] = "degraded"
        else:
            health["checks"]["redis"] = "not configured"
        
        status_code = 200 if health["status"] == "healthy" else 503
        return jsonify(health), status_code

    # Request ID middleware for tracing
    @app.before_request
    def add_request_id():
        import uuid
        request.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.after_request
    def add_response_headers(response):
        response.headers['X-Request-ID'] = getattr(request, 'request_id', 'unknown')
        return response

    return app


if __name__ == '__main__':
    app = create_app()
    debug = settings.DEBUG
    
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not debug:
        from reminders import start_reminder_scheduler
        start_reminder_scheduler(app)
        from retrain_scheduler import start_retrain_scheduler
        start_retrain_scheduler(app)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug, host='0.0.0.0', port=port)