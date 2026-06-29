"""Backward-compatible authentication service shim."""

from app.application.services.authentication_service import (
    ACCESS_COOKIE_NAME as ACCESS_COOKIE,
)
from app.application.services.authentication_service import (
    REFRESH_COOKIE_NAME as REFRESH_COOKIE,
)
from app.application.services.authentication_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_optional_user,
    get_user_from_access_token,
    hash_password,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
    verify_password,
)

__all__ = [
    "ACCESS_COOKIE",
    "REFRESH_COOKIE",
    "authenticate_user",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "get_optional_user",
    "get_user_from_access_token",
    "hash_password",
    "register_user",
    "revoke_refresh_token",
    "rotate_refresh_token",
    "verify_password",
]
