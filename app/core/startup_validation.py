"""Production startup validation for critical settings."""

from app.core.configuration import Settings

_WEAK_JWT_SECRETS = frozenset(
    {
        "",
        "change-me-in-production",
        "changeme",
        "secret",
    }
)
_MIN_JWT_SECRET_BYTES = 32


def validate_production_settings(settings: Settings) -> None:
    """Validate settings required for non-debug deployments."""
    if settings.debug:
        return

    secret = settings.jwt_secret_key.strip()
    if secret in _WEAK_JWT_SECRETS:
        message = (
            "JWT_SECRET_KEY is missing or uses a known weak default. "
            "Set a strong secret (e.g. openssl rand -hex 32) before running "
            "with DEBUG=false."
        )
        raise RuntimeError(message)

    if len(secret.encode()) < _MIN_JWT_SECRET_BYTES:
        message = (
            f"JWT_SECRET_KEY must be at least {_MIN_JWT_SECRET_BYTES} bytes when "
            "DEBUG=false."
        )
        raise RuntimeError(message)

    if not settings.google_api_key.strip():
        message = (
            "GOOGLE_API_KEY is required when DEBUG=false. "
            "Set it in the environment before starting the application."
        )
        raise RuntimeError(message)
