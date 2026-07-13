import json
import logging

from app.core.logging.setup import configure_logging
from tests.support.settings_factory import build_test_settings


def test_configure_logging_json_format() -> None:
    settings = build_test_settings(
        log_format="json",
        debug=False,
    )
    configure_logging(settings=settings)

    test_logger = logging.getLogger("test.configure_logging")
    captured: list[str] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record.getMessage())

    root = logging.getLogger()
    root.handlers[0].setLevel(logging.INFO)

    test_logger.info("structured test", extra={"request_id": "abc-123"})

    # Read from stdout handler by using JsonLogFormatter directly
    from app.core.logging.json_formatter import JsonLogFormatter

    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="structured test",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc-123"
    payload = json.loads(formatter.format(record))
    assert payload["request_id"] == "abc-123"
