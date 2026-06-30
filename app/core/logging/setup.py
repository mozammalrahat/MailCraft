"""Application logging configuration."""

import logging
import sys

from app.core.configuration import Settings
from app.core.logging.filters import RequestContextFilter
from app.core.logging.json_formatter import JsonLogFormatter


def configure_logging(settings: Settings | None = None) -> None:
    """Configure root logging for the application."""
    from app.core.configuration import get_settings

    resolved = settings or get_settings()
    level_name = resolved.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestContextFilter())

    if resolved.effective_log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s "
                "[request_id=%(request_id)s] %(message)s",
                defaults={"request_id": "-"},
            )
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING if not resolved.debug else logging.INFO
    )
