"""Exception handlers for the MailCraft application."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import LlmError, ServiceValidationError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LlmError)
    async def handle_llm_error(_: Request, exc: LlmError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": exc.message},
        )

    @app.exception_handler(ServiceValidationError)
    async def handle_validation_error(
        _: Request, exc: ServiceValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def handle_unhandled_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = getattr(getattr(request, "state", None), "request_id", None)
        logger.exception(
            "Unhandled exception",
            exc_info=exc,
            extra={"request_id": request_id, "path": request.url.path},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
