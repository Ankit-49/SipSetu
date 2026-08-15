"""OpenAPI/Swagger documentation (Phase 4.1).

The API blueprint is registered twice — canonical ``/api/{API_VERSION}`` and
the legacy unversioned ``/api`` prefix (see ``app.py``). Flasgger builds the
spec from YAML docstrings on the route functions; the legacy registration is
excluded via ``rule_filter`` so the docs only describe the versioned surface.

Request/response schemas are defined once here (the OpenAPI ``definitions``
section) and referenced from route docstrings with ``$ref``, keeping the
source of truth for API shapes in a single place.
"""

from config import settings


def build_swagger(app):
    """Attach the Flasgger Swagger UI + OpenAPI spec to ``app``.

    The UI is served locally at ``/apidocs/`` (no CDN dependency) and the
    machine-readable spec at ``/apispec.json``. Only routes with a YAML
    docstring appear in the spec — currently the auth endpoints; more routes
    can be added by giving them a ``---`` YAML docstring block.
    """
    from flasgger import Swagger

    config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec.json",
                # Only document the canonical /api/v1 registration, never the
                # legacy /api alias (endpoints registered with name='api_legacy').
                "rule_filter": lambda rule: not rule.endpoint.startswith(
                    "api_legacy."
                ),
                "model_filter": lambda tag: True,
            }
        ],
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }

    template = {
        "info": {
            "title": f"{settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "description": (
                f"REST API for {settings.APP_NAME}. All endpoints live under "
                f"/api/{settings.API_VERSION}. The legacy unversioned /api "
                "prefix is deprecated and carries Deprecation/Sunset headers; "
                "it will be retired after the advertised Sunset date."
            ),
        },
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": (
                    "JWT access token returned by "
                    f"/api/{settings.API_VERSION}/auth/login or "
                    f"/api/{settings.API_VERSION}/auth/register. "
                    'Sent as "Bearer <token>".'
                ),
            }
        },
        "definitions": {
            # ------------------------------------------------------------------
            # Shared shapes
            # ------------------------------------------------------------------
            "Error": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "Human-readable error message",
                    }
                },
            },
            "AuthResponse": {
                "type": "object",
                "required": ["message", "token", "user_id", "role", "email"],
                "properties": {
                    "message": {"type": "string"},
                    "token": {"type": "string", "description": "JWT access token"},
                    "user_id": {"type": "string", "format": "uuid"},
                    "role": {"type": "string", "enum": ["applicant", "recruiter"]},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "email_verified": {"type": "boolean"},
                },
            },
            # ------------------------------------------------------------------
            # Auth request schemas
            # ------------------------------------------------------------------
            "RegisterRequest": {
                "type": "object",
                "required": ["email", "password", "role"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {
                        "type": "string",
                        "minLength": 8,
                        "maxLength": 128,
                    },
                    "role": {"type": "string", "enum": ["applicant", "recruiter"]},
                    "name": {"type": "string", "maxLength": 255},
                },
            },
            "LoginRequest": {
                "type": "object",
                "required": ["email", "password"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "password": {"type": "string"},
                },
            },
            "VerifyEmailRequest": {
                "type": "object",
                "required": ["email", "otp"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "otp": {
                        "type": "string",
                        "description": "6-digit code sent to the email",
                        "minLength": 6,
                        "maxLength": 6,
                    },
                },
            },
            "ForgotPasswordRequest": {
                "type": "object",
                "required": ["email"],
                "properties": {"email": {"type": "string", "format": "email"}},
            },
            "VerifyOTPRequest": {
                "type": "object",
                "required": ["email", "otp"],
                "properties": {
                    "email": {"type": "string", "format": "email"},
                    "otp": {
                        "type": "string",
                        "description": "6-digit code sent to the email",
                        "minLength": 6,
                        "maxLength": 6,
                    },
                },
            },
            "ResetPasswordRequest": {
                "type": "object",
                "required": ["token", "email", "password"],
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "reset_token from /auth/verify-reset-otp",
                    },
                    "email": {"type": "string", "format": "email"},
                    "password": {
                        "type": "string",
                        "minLength": 8,
                        "maxLength": 128,
                    },
                },
            },
            # ------------------------------------------------------------------
            # Auth response schemas
            # ------------------------------------------------------------------
            "MeResponse": {
                "type": "object",
                "required": ["user_id", "email", "role"],
                "properties": {
                    "user_id": {"type": "string", "format": "uuid"},
                    "email": {"type": "string", "format": "email"},
                    "name": {"type": "string"},
                    "role": {"type": "string", "enum": ["applicant", "recruiter"]},
                    "phone": {"type": "string"},
                    "location": {"type": "string"},
                    "profile_image": {"type": "string"},
                    "email_verified": {"type": "boolean"},
                    "company": {"type": "string"},
                    "job_title": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                },
            },
            "VerifyEmailResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "email_verified": {"type": "boolean"},
                },
            },
            "ForgotPasswordResponse": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            "VerifyResetOTPResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "reset_token": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                },
            },
            "ResetPasswordResponse": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
            "ResendVerificationResponse": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "expires_at": {
                        "type": "string",
                        "description": "OTP expiry timestamp (ISO 8601, UTC)",
                    },
                },
            },
            "LogoutResponse": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
            },
        },
    }

    swagger = Swagger(app, config=config, template=template)
    app.swagger = swagger
    return swagger
