"""Backward-compatible stateful generation shim."""

from app.application.handlers.application_document_handler import (
    ApplicationDocumentHandler,
)
from app.schemas.generated_content import GeneratedContentResponse

_handler = ApplicationDocumentHandler()


async def generate_stateful_document(*args, **kwargs) -> GeneratedContentResponse:
    """Delegate to application document handler."""
    return await _handler.generate(*args, **kwargs)
