"""Serialize generated content ORM rows for API responses."""

from app.application.services.email_formatting_service import build_clipboard_text
from app.database.models.generated_content import GeneratedContent
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.schemas.generated_content import GeneratedContentResponse


def serialize_generated_content(
    record: GeneratedContent,
    *,
    include_raw_content: bool = False,
) -> GeneratedContentResponse:
    """Convert a generated content ORM instance to API response."""
    purpose = (
        ApplicationPurpose(record.purpose) if record.purpose else None
    )
    document_type = (
        DocumentType(record.document_type) if record.document_type else None
    )
    scenario_name = ""
    if record.scenario is not None:
        scenario_name = record.scenario.name

    raw_subject = record.raw_subject if include_raw_content else None
    raw_body = record.raw_body if include_raw_content else None

    return GeneratedContentResponse(
        id=record.id,
        generation_kind=GenerationKind(record.generation_kind),
        purpose=purpose,
        document_type=document_type,
        scenario_id=record.scenario_id,
        scenario_name=scenario_name,
        position_description=record.position_description,
        grounding_links=record.grounding_links,
        cv_filenames=record.cv_filenames,
        intent=record.intent,
        key_facts=record.key_facts,
        tone=record.tone,
        strategy=record.strategy,
        subject=record.subject,
        body=record.body,
        raw_subject=raw_subject,
        raw_body=raw_body,
        humanization_applied=record.humanization_applied,
        clipboard_text=build_clipboard_text(subject=record.subject, body=record.body),
        metadata_json=record.document_metadata,
        created_at=record.created_at,
    )
