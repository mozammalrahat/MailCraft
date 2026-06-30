"""JSON log formatter for machine-parseable stdout logs."""

import json
import logging
from datetime import UTC, datetime

_RESERVED_RECORD_KEYS = frozenset(
    logging.makeLogRecord({}).__dict__.keys()
) | frozenset({"message", "asctime"})


class JsonLogFormatter(logging.Formatter):
    """Emit one JSON object per log record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_RECORD_KEYS:
                continue
            if key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)
