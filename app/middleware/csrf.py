"""CSRF protection middleware using the double-submit cookie pattern.

All non-API POST/PUT/DELETE/PATCH routes must include a hidden ``csrf_token``
form field whose value matches the ``csrf_token`` cookie set on the preceding
GET request.  API routes (``/api/*``) and static assets are exempt.

Set ``CSRF_ENABLED=false`` in the environment to disable (e.g. in tests).
"""

import logging
import secrets
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.csrf import (
    _SAFE_METHODS,
    CSRF_COOKIE_NAME,
    CSRF_FORM_FIELD,
    generate_csrf_token,
    is_csrf_exempt,
)

logger = logging.getLogger(__name__)

_FORM_CONTENT_TYPES = (
    "application/x-www-form-urlencoded",
    "multipart/form-data",
)


class CsrfMiddleware(BaseHTTPMiddleware):
    """Validate CSRF tokens on mutating HTML-form requests."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        csrf_enabled: bool = True,
        debug: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(app, **kwargs)
        self._csrf_enabled = csrf_enabled
        self._secure = not debug

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self._csrf_enabled or is_csrf_exempt(request.url.path):
            request.state.csrf_token = ""
            return await call_next(request)

        csrf_token = request.cookies.get(CSRF_COOKIE_NAME) or generate_csrf_token()
        request.state.csrf_token = csrf_token

        if request.method not in _SAFE_METHODS:
            content_type = request.headers.get("content-type", "")
            is_form = any(ct in content_type for ct in _FORM_CONTENT_TYPES)

            if is_form:
                # Buffer and replay the body so downstream Form() parsing still works.
                # BaseHTTPMiddleware + request.form() otherwise consumes the stream.
                body = await request.body()

                async def receive():
                    return {"type": "http.request", "body": body, "more_body": False}

                request = Request(request.scope, receive)
                request.state.csrf_token = csrf_token

                try:
                    form = await request.form()
                    form_token = str(form.get(CSRF_FORM_FIELD, ""))
                except Exception:
                    form_token = ""

                cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
                valid = bool(
                    cookie_token
                    and form_token
                    and secrets.compare_digest(cookie_token, form_token)
                )
                if not valid:
                    logger.warning(
                        "CSRF validation failed",
                        extra={"path": request.url.path, "method": request.method},
                    )
                    return Response(
                        "CSRF token mismatch — please reload the page and try again.",
                        status_code=403,
                        media_type="text/plain",
                    )

        response = await call_next(request)

        if CSRF_COOKIE_NAME not in request.cookies:
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=csrf_token,
                httponly=True,
                samesite="strict",
                secure=self._secure,
            )

        return response
