import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config, settings

# Logging
from logging_config import log_request_middleware, setup_logging
from models import db

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

try:
    from prometheus_flask_exporter import PrometheusMetrics
    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Sentry error tracking (only when SENTRY_DSN is configured)
    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FlaskIntegration()],
                environment=settings.ENVIRONMENT,
                release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
                traces_sample_rate=0.1,
                profiles_sample_rate=0.0,
                send_default_pii=False,
            )
        except Exception as e:
            app.logger.warning(f"Failed to initialize Sentry: {e}")

    # Configure logging first
    setup_logging(app)
    log_request_middleware(app)

    # Distributed tracing (OpenTelemetry) — no-op unless OTEL_ENABLED=true.
    # tracing.setup_tracing() handles missing packages internally.
    from tracing import setup_tracing
    setup_tracing(app)

    # Configure CORS with explicit origins
    # FRONTEND_URL can be comma-separated for multiple origins
    frontend_urls = [u.strip() for u in settings.FRONTEND_URL.split(',') if u.strip()]
    # Always allow Cloudflare Pages and preview deployments
    extra_origins = ['https://sipsetu.pages.dev', 'https://*.sipsetu.pages.dev']
    cors_origins = list(dict.fromkeys(frontend_urls + extra_origins))
    CORS(app, origins=cors_origins, supports_credentials=True)

    app.config.from_object(Config)

    # Database configuration
    db_url = settings.DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if db_url.startswith('sqlite'):
        # SQLite (tests) does not support pool_size/max_overflow
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
    else:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': settings.DB_POOL_RECYCLE,
            'pool_size': settings.DB_POOL_SIZE,
            'max_overflow': settings.DB_MAX_OVERFLOW,
        }

    db.init_app(app)

    # Phase 6.4 — Internationalization (Flask-Babel)
    try:
        from i18n import init_babel
        init_babel(app)
    except Exception as babel_err:
        app.logger.warning(f"Flask-Babel init failed (non-fatal): {babel_err}")

    # Security headers with Talisman (production only)
    if HAS_TALISMAN and not app.debug and settings.ENVIRONMENT == 'production':
        csp = {
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'", "https:", "data:"],
            'connect-src': ["'self'", *cors_origins],
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

    # Register routes — canonical versioned prefix (/api/v1) plus the legacy
    # unversioned prefix (/api), which stays live until the Sunset date but is
    # marked deprecated via RFC 8594 headers (Phase 4.1).
    from routes import api
    app.register_blueprint(api, url_prefix=f'/api/{settings.API_VERSION}')
    app.register_blueprint(api, url_prefix='/api', name='api_legacy')

    # Phase 5 routes (LLM parsing, feedback, admin, notifications)
    from routes_phase5 import phase5
    app.register_blueprint(phase5, url_prefix=f'/api/{settings.API_VERSION}')
    app.register_blueprint(phase5, url_prefix='/api', name='phase5_legacy')

    # Phase 6.1 — Organization & team management routes
    from routes_organizations import orgs_bp
    app.register_blueprint(orgs_bp, url_prefix=f'/api/{settings.API_VERSION}')
    app.register_blueprint(orgs_bp, url_prefix='/api', name='orgs_legacy')

    # Phase 6.2 — Advanced matching: semantic search & market intelligence
    from routes_phase6 import phase6
    app.register_blueprint(phase6, url_prefix=f'/api/{settings.API_VERSION}')
    app.register_blueprint(phase6, url_prefix='/api', name='phase6_legacy')

    # Phase 6.3 — Integrations: ATS sync, Calendar, Communication, SSO
    from routes_integrations import phase63
    app.register_blueprint(phase63, url_prefix=f'/api/{settings.API_VERSION}')
    app.register_blueprint(phase63, url_prefix='/api', name='phase63_legacy')

    # Phase 6.4 — Internationalization
    from routes_i18n import i18n_bp
    app.register_blueprint(i18n_bp, url_prefix=f'/api/{settings.API_VERSION}')
    app.register_blueprint(i18n_bp, url_prefix='/api', name='i18n_legacy')

    # Phase 5.3 — Initialize WebSocket (Flask-SocketIO) for real-time notifications.
    # init_socketio() is a no-op when flask-socketio is not installed.
    from websocket import init_socketio
    socketio = init_socketio(app)
    app.socketio = socketio

    # OpenAPI/Swagger documentation (Phase 4.1) — documents the /api/v1 surface
    # only; the legacy /api endpoints are excluded from the spec.
    if settings.SWAGGER_ENABLED:
        try:
            from api_docs import build_swagger
            build_swagger(app)
        except Exception as e:
            app.logger.warning(f"Failed to initialize Swagger docs: {e}")

    # Prometheus metrics (exposes /metrics)
    if HAS_METRICS and settings.METRICS_ENABLED:
        try:
            metrics = PrometheusMetrics(
                app,
                metrics_decorator=None,
                default_labels={
                    'app': settings.APP_NAME,
                    'version': settings.APP_VERSION,
                },
                group_by='endpoint',
            )
            app.metrics = metrics
        except Exception as e:
            app.logger.warning(f"Failed to initialize Prometheus metrics: {e}")

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
            db.session.execute(db.text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS organization_id UUID"))
            db.session.execute(db.text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS embedding TEXT"))
            db.session.execute(db.text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS embedding TEXT"))
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS locale VARCHAR(10)"))
            # Phase 6.3 — integration tables created via migration 009;
            # on SQLite (dev/tests) we create them inline since Alembic is
            # not invoked at startup.
            try:
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS ats_connections (
                        connection_id VARCHAR(36) PRIMARY KEY,
                        recruiter_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        provider VARCHAR(50) NOT NULL,
                        api_key_encrypted TEXT NOT NULL,
                        webhook_secret VARCHAR(128),
                        ats_org_id VARCHAR(255),
                        sync_status VARCHAR(20) DEFAULT 'idle',
                        last_synced_at DATETIME,
                        sync_cursor TEXT,
                        config TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS webhook_subscriptions (
                        subscription_id VARCHAR(36) PRIMARY KEY,
                        connection_id VARCHAR(36) NOT NULL REFERENCES ats_connections(connection_id) ON DELETE CASCADE,
                        event_type VARCHAR(100) NOT NULL,
                        target_url TEXT NOT NULL,
                        secret VARCHAR(255) NOT NULL,
                        is_active BOOLEAN DEFAULT 1,
                        last_triggered_at DATETIME,
                        failure_count INTEGER DEFAULT 0,
                        created_at DATETIME
                    )
                """))
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS oauth_tokens (
                        token_id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        provider VARCHAR(50) NOT NULL,
                        scopes TEXT NOT NULL,
                        access_token_encrypted TEXT NOT NULL,
                        refresh_token_encrypted TEXT,
                        token_expiry DATETIME NOT NULL,
                        calendar_id VARCHAR(255),
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS calendar_events (
                        event_id VARCHAR(36) PRIMARY KEY,
                        interview_id VARCHAR(36) NOT NULL REFERENCES interviews(interview_id) ON DELETE CASCADE,
                        oauth_token_id VARCHAR(36) NOT NULL REFERENCES oauth_tokens(token_id) ON DELETE CASCADE,
                        external_event_id VARCHAR(255),
                        provider VARCHAR(50) NOT NULL,
                        sync_status VARCHAR(20) DEFAULT 'pending',
                        last_synced_at DATETIME,
                        created_at DATETIME
                    )
                """))
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS communication_channels (
                        channel_id VARCHAR(36) PRIMARY KEY,
                        recruiter_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        provider VARCHAR(50) NOT NULL,
                        webhook_url TEXT NOT NULL,
                        channel_name VARCHAR(255),
                        channel_id_external VARCHAR(255),
                        events_subscribed TEXT DEFAULT 'application.received,application.shortlisted',
                        is_active BOOLEAN DEFAULT 1,
                        last_notified_at DATETIME,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                db.session.execute(db.text("""
                    CREATE TABLE IF NOT EXISTS sso_providers (
                        provider_id VARCHAR(36) PRIMARY KEY,
                        organization_id VARCHAR(36) REFERENCES organizations(org_id) ON DELETE CASCADE,
                        name VARCHAR(255) NOT NULL,
                        protocol VARCHAR(20) NOT NULL,
                        issuer TEXT NOT NULL,
                        client_id VARCHAR(255),
                        client_secret_encrypted TEXT,
                        metadata_url TEXT,
                        metadata_xml TEXT,
                        certificate TEXT,
                        redirect_url TEXT NOT NULL,
                        auto_provision BOOLEAN DEFAULT 1,
                        default_role VARCHAR(50) DEFAULT 'viewer',
                        is_active BOOLEAN DEFAULT 1,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
            except Exception:
                pass  # tables already exist
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
            try:
                from metrics import gauge_set
                pool = db.engine.pool
                checkedout = getattr(pool, "checkedout", None)
                overflow = getattr(pool, "overflow", None)
                size = getattr(pool, "size", None)
                # QueuePool (Postgres) exposes these; StaticPool (sqlite tests) does not.
                if checkedout is not None:
                    gauge_set(app, "sipsetu_db_pool_checkedout", "SQLAlchemy pool connections checked out", checkedout())
                if overflow is not None:
                    gauge_set(app, "sipsetu_db_pool_overflow", "SQLAlchemy pool overflow connections", overflow())
                if size is not None:
                    gauge_set(app, "sipsetu_db_pool_size", "SQLAlchemy pool configured size", size())
            except Exception as pool_err:
                app.logger.warning(f"Failed to report DB pool metrics: {pool_err}")
        except Exception as e:
            health["checks"]["database"] = f"failed: {str(e)[:100]}"
            health["status"] = "degraded"
        
        # Redis check (if configured)
        redis_url = settings.REDIS_URL
        redis_up = 0.0
        if redis_url and HAS_REDIS:
            try:
                r = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
                r.ping()
                health["checks"]["redis"] = "ok"
                redis_up = 1.0
            except Exception as e:
                health["checks"]["redis"] = f"failed: {str(e)[:100]}"
                health["status"] = "degraded"
        else:
            health["checks"]["redis"] = "not configured"
        try:
            from metrics import gauge_set
            gauge_set(app, "sipsetu_redis_up", "Redis reachability (1 = up, 0 = down)", redis_up)
        except Exception as gauge_err:
            app.logger.warning(f"Failed to report Redis metric: {gauge_err}")
        
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

    @app.after_request
    def add_api_deprecation_headers(response):
        """RFC 8594 deprecation headers for the legacy unversioned /api prefix.

        The canonical surface is /api/v1/*. Requests hitting the legacy
        /api/* alias (except the unversioned infra endpoint /api/health) get
        Deprecation: true, a Sunset date, and a Link to the v1 successor.
        """
        path = request.path
        if (
            path.startswith("/api/")
            and path != "/api/health"
            and not path.startswith(f"/api/{settings.API_VERSION}/")
        ):
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = settings.API_DEPRECATION_DATE
            successor = f"/api/{settings.API_VERSION}{path[len('/api'):]}"
            response.headers["Link"] = f'<{successor}>; rel="successor-version"'
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
    socketio = getattr(app, 'socketio', None)
    if socketio:
        # Use Flask-SocketIO's server which supports both HTTP and WebSocket
        socketio.run(app, debug=debug, host='0.0.0.0', port=port)
    else:
        app.run(debug=debug, host='0.0.0.0', port=port)