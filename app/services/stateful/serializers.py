"""Backward-compatible serializer shim."""

from app.application.serializers.generated_content_serializer import (
    serialize_generated_content as document_to_out,
)

__all__ = ["document_to_out"]
