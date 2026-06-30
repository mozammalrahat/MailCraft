"""CSRF protection utilities using the double-submit cookie pattern."""

import secrets

CSRF_COOKIE_NAME = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
_API_PREFIX = "/api/"
_STATIC_PREFIX = "/static/"


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(32)


def is_csrf_exempt(path: str) -> bool:
    """Return True for routes that do not require CSRF validation."""
    return path.startswith(_API_PREFIX) or path.startswith(_STATIC_PREFIX)
