from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes.api.auth_api import router as authentication_api_router
from app.api.routes.api.email import router as email_generation_router
from app.api.routes.api.generations import router as generated_content_router
from app.api.routes.api.health import router as health_router
from app.api.routes.api.jobs import router as jobs_router
from app.api.routes.api.scenarios import router as scenario_router
from app.api.routes.auth_pages import router as authentication_page_router
from app.api.routes.dashboard.pages import router as dashboard_router
from app.api.routes.pages import router as page_router
from app.core.configuration import get_settings
from app.core.rate_limits import limiter
from app.core.startup_validation import validate_production_settings
from app.database.engine_manager import get_database_engine_manager, initialize_database
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.csrf import CsrfMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    validate_production_settings(settings)
    configure_logging(settings=settings)
    initialize_database()
    yield
    get_database_engine_manager().dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    limiter.enabled = settings.rate_limit_enabled

    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(
        CsrfMiddleware, csrf_enabled=settings.csrf_enabled, debug=settings.debug
    )
    application.add_middleware(SecurityHeadersMiddleware)
    register_exception_handlers(application)

    if STATIC_DIRECTORY.is_dir():
        application.mount(
            "/static",
            StaticFiles(directory=STATIC_DIRECTORY),
            name="static",
        )

    application.include_router(health_router, prefix="/api")
    application.include_router(jobs_router, prefix="/api")
    application.include_router(email_generation_router, prefix="/api")
    application.include_router(authentication_api_router, prefix="/api")
    application.include_router(scenario_router, prefix="/api")
    application.include_router(generated_content_router, prefix="/api")
    application.include_router(authentication_page_router)
    application.include_router(dashboard_router)
    application.include_router(page_router)

    return application


app = create_app()


def run() -> None:
    """Run the MailCraft web server."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
