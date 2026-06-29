"""Parse and validate humanized content from language model output."""


from app.application.services.email_formatting_service import format_document_body
from app.application.services.email_generation_service import parse_legacy_email_output
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind

_NONE_SUBJECT_VALUES = {"(none)", "none", "n/a", ""}


def resolve_content_type_label(
    generation_kind: GenerationKind,
    document_type: DocumentType | None,
) -> str:
    """Return a human-readable label for the humanizer prompt."""
    if generation_kind == GenerationKind.LEGACY_EMAIL:
        return "Professional email"
    if document_type == DocumentType.COVER_LETTER:
        return "Cover letter"
    return "Application email"


def parse_humanized_output(raw_output: str) -> tuple[str | None, str]:
    """Parse subject and body from a humanizer response."""
    subject, body = parse_legacy_email_output(raw_output)
    normalized_subject = _normalize_subject(subject)
    formatted_body = format_document_body(body)
    return normalized_subject, formatted_body


def _normalize_subject(subject: str | None) -> str | None:
    """Normalize subject placeholders from the humanizer."""
    if subject is None:
        return None
    cleaned = subject.strip()
    if cleaned.lower() in _NONE_SUBJECT_VALUES:
        return None
    return cleaned
