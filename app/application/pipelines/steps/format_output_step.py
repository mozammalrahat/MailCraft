"""Format generated output."""

from app.application.pipelines.generation_context import GenerationContext
from app.application.services.email_formatting_service import (
    build_clipboard_text,
    format_document_body,
    resolve_subject_and_body,
)
from app.application.services.email_generation_service import parse_legacy_email_output
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.schemas.application_document import StructuredApplicationDocumentOutput
from app.services.errors import LlmError


class FormatOutputStep:
    """Normalize subject and body formatting."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Format subject, body, and clipboard text."""
        if context.validation_errors:
            return context

        if context.generation_kind == GenerationKind.LEGACY_EMAIL:
            subject, body = parse_legacy_email_output(context.raw_language_model_output)
            formatted_body = format_document_body(body)
            context.subject = subject
            context.body = formatted_body
            context.clipboard_text = build_clipboard_text(
                subject=subject,
                body=formatted_body,
            )
            return context

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
