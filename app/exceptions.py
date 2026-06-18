from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.errors import LlmError, ServiceValidationError


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
