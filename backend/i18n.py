"""Flask-Babel internationalization setup (Phase 6.4).

Provides:
- Lazy gettext / lazy ngettext helpers
- Locale detection from Accept-Language header, user preference, and query param
- Translation catalogue extraction via ``pybabel extract``
"""

from flask_babel import Babel, get_locale, lazy_gettext

# Supported locales: code -> (native name, English name)
SUPPORTED_LOCALES: dict[str, tuple[str, str]] = {
    "en": ("English", "English"),
    "hi": ("हिन्दी", "Hindi"),
    "es": ("Español", "Spanish"),
    "fr": ("Français", "French"),
    "de": ("Deutsch", "German"),
    "pt": ("Português", "Portuguese"),
    "ar": ("العربية", "Arabic"),
    "zh": ("中文", "Chinese"),
    "ja": ("日本語", "Japanese"),
    "ko": ("한국어", "Korean"),
}

DEFAULT_LOCALE = "en"


def _locale_selector() -> str:
    """Resolve the user's preferred locale.

    Priority:
    1. ``?lang=`` query parameter (for quick switching during development)
    2. ``Accept-Language`` header from the browser
    3. User's saved preference (from DB, injected by auth middleware)
    4. Falls back to DEFAULT_LOCALE
    """
    from flask import g, request

    # 1. Explicit query param override
    lang = request.args.get("lang")
    if lang and lang in SUPPORTED_LOCALES:
        return lang

    # 2. Accept-Language header
    best = request.accept_languages.best_match(
        list(SUPPORTED_LOCALES.keys())
    )
    if best:
        return best

    # 3. User preference stored on g (set by auth middleware)
    user_locale = getattr(g, "user_locale", None)
    if user_locale and user_locale in SUPPORTED_LOCALES:
        return user_locale

    return DEFAULT_LOCALE


def init_babel(app):
    """Initialise Flask-Babel on the given Flask app."""
    babel = Babel(
        app,
        locale_selector=_locale_selector,
        default_locale=DEFAULT_LOCALE,
    )

    @app.before_request
    def _inject_locale_to_g():
        """Store resolved locale on g for templates / other middleware."""
        from flask import g
        g.locale = str(get_locale())

    return babel
