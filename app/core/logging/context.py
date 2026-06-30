"""Request-scoped logging context."""

from contextvars import ContextVar, Token

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def bind_request_id(request_id: str) -> Token[str | None]:
    """Bind a request ID to the current context."""
    return _request_id.set(request_id)


def get_request_id() -> str | None:
    """Return the current request ID, if any."""
    return _request_id.get()


def clear_request_id(token: Token[str | None] | None = None) -> None:
    """Clear the bound request ID."""
    if token is not None:
        _request_id.reset(token)
        return
    _request_id.set(None)
