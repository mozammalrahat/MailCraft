"""Shared rate limiter configuration."""

from app.application.services.authentication_service import (
    ACCESS_COOKIE_NAME,
    decode_token,
)
from app.core.configuration import get_settings
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def authenticated_rate_limit_key(request: Request) -> str:
    """Rate limit authenticated generation routes by user when possible."""
    settings = get_settings()
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if token:
        try:
            payload = decode_token(token, settings)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)
