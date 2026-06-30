import json
import logging

from app.core.logging.json_formatter import JsonLogFormatter

logger = logging.getLogger("test.json_formatter")


def test_json_formatter_includes_message_and_extras() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"
    record.latency_ms = 42

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "hello"
    assert payload["request_id"] == "req-123"
    assert payload["latency_ms"] == 42
    assert payload["level"] == "INFO"
