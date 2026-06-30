"""Logging filters for request correlation."""

import logging

from app.core.logging.context import get_request_id


class RequestContextFilter(logging.Filter):
    """Inject request_id from context into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        request_id = get_request_id()
        if request_id is not None:
            record.request_id = request_id
        return True
