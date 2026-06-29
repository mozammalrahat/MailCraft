from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.configuration import get_settings
from app.database.engine_manager import get_database_engine_manager, initialize_database
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers.api.auth_api import router as authentication_api_router
from app.routers.api.email import router as email_generation_router
from app.routers.api.generations import router as generated_content_router
from app.routers.api.health import router as health_router
from app.routers.api.scenarios import router as scenario_router
from app.routers.auth_pages import router as authentication_page_router
from app.routers.dashboard.pages import router as dashboard_router
from app.routers.pages import router as page_router

STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    configure_logging(debug=settings.debug)
    initialize_database()
    yield
    get_database_engine_manager().dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    application.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(application)

    if STATIC_DIRECTORY.is_dir():
        application.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")

    application.include_router(health_router, prefix="/api")
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
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8081,
        reload=get_settings().debug,
    )


if __name__ == "__main__":
    run()
