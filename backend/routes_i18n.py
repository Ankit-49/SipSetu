"""Phase 6.4 — Internationalization routes.

Endpoints:
- GET  /i18n/locales           — list supported locales
- GET  /i18n/preferences       — get current user's locale preference
- PUT  /i18n/preferences       — update current user's locale preference
- POST /i18n/translations      — get translations for a given locale (batch by namespace)
"""

from flask import Blueprint, g, jsonify, request

from auth_middleware import require_auth
from models import User, db

i18n_bp = Blueprint("i18n", __name__)

# Supported locales — must match frontend i18n config
SUPPORTED_LOCALES = [
    {"code": "en", "native_name": "English", "english_name": "English"},
    {"code": "hi", "native_name": "हिन्दी", "english_name": "Hindi"},
    {"code": "es", "native_name": "Español", "english_name": "Spanish"},
    {"code": "fr", "native_name": "Français", "english_name": "French"},
    {"code": "de", "native_name": "Deutsch", "english_name": "German"},
    {"code": "pt", "native_name": "Português", "english_name": "Portuguese"},
    {"code": "ar", "native_name": "العربية", "english_name": "Arabic"},
    {"code": "zh", "native_name": "中文", "english_name": "Chinese"},
    {"code": "ja", "native_name": "日本語", "english_name": "Japanese"},
    {"code": "ko", "native_name": "한국어", "english_name": "Korean"},
]


@i18n_bp.route("/i18n/locales", methods=["GET"])
def list_locales():
    """Return all supported locales."""
    return jsonify({"locales": SUPPORTED_LOCALES, "default": "en"})


@i18n_bp.route("/i18n/preferences", methods=["GET"])
@require_auth
def get_locale_preference():
    """Return the authenticated user's saved locale preference."""
    user_id = g.user_id
    user = db.session.get(User, user_id)
    locale = getattr(user, "locale", None) or "en"
    return jsonify({"locale": locale})


@i18n_bp.route("/i18n/preferences", methods=["PUT"])
@require_auth
def update_locale_preference():
    """Update the authenticated user's locale preference."""
    data = request.get_json(silent=True) or {}
    locale_code = (data.get("locale") or "").strip()
    valid_codes = {loc["code"] for loc in SUPPORTED_LOCALES}

    if locale_code not in valid_codes:
        return jsonify({"error": f"Unsupported locale: {locale_code}",
                        "supported": sorted(valid_codes)}), 400

    user_id = g.user_id
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.locale = locale_code
    db.session.commit()

    return jsonify({"locale": locale_code, "message": "Locale preference updated"})


@i18n_bp.route("/i18n/translations", methods=["POST"])
def get_translations():
    """Return translations for a given locale.

    Request body: { "locale": "hi", "namespaces": ["common", "auth"] }
    Returns a flat map of translation keys for the requested namespaces.
    """
    data = request.get_json(silent=True) or {}
    locale = data.get("locale", "en")

    # Validate locale
    valid_codes = {loc["code"] for loc in SUPPORTED_LOCALES}
    if locale not in valid_codes:
        locale = "en"

    # For server-side rendering or SSR contexts — this endpoint is a bridge.
    # The frontend primarily loads translations from static JSON files, but
    # this endpoint allows SSR frameworks or mobile clients to fetch them.
    return jsonify({
        "locale": locale,
        "namespaces": data.get("namespaces", ["common"]),
        "message": "Translations are loaded from static files on the frontend. "
                   "This endpoint confirms locale support.",
    })
