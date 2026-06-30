"""Format generated output."""

from app.application.pipelines.generation_context import GenerationContext
from app.application.services.email_formatting_service import (
    build_clipboard_text,
    format_document_body,
    resolve_subject_and_body,
)
from app.core.exceptions import LlmError
from app.domain.enums.document_type import DocumentType
from app.schemas.application_document import StructuredApplicationDocumentOutput


class FormatOutputStep:
    """Normalize subject and body formatting."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Format subject, body, and clipboard text."""
        output = StructuredApplicationDocumentOutput.model_validate(
            context.structured_output
        )
        subject, raw_body = resolve_subject_and_body(
            output.body,
            output.subject.strip() or None,
        )
        formatted_body = format_document_body(raw_body)

        if (
            context.document_type == DocumentType.EMAIL
            and not subject
        ):
            raise LlmError("Generated email is missing a subject line")

        context.subject = subject
        context.body = formatted_body
        context.document_metadata = output.metadata.model_dump()
        context.clipboard_text = build_clipboard_text(
            subject=subject,
            body=formatted_body,
        )
        return context
