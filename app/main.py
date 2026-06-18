from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.routers.api.email import router as email_router
from app.routers.api.evaluation import router as evaluation_router
from app.routers.api.health import router as health_router
from app.routers.pages import router as pages_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(debug=settings.debug)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    app.include_router(health_router, prefix="/api")
    app.include_router(email_router, prefix="/api")
    app.include_router(evaluation_router, prefix="/api")
    app.include_router(pages_router)

    return app


app = create_app()


def run() -> None:
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=get_settings().debug,
    )


if __name__ == "__main__":
    run()
