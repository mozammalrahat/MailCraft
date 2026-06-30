from datetime import UTC, datetime

from app.database.models.generated_content import GeneratedContent
from app.database.models.scenario import Scenario
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.export.document_pdf_exporter import (
    build_document_pdf,
    pdf_filename,
)


def _sample_document() -> GeneratedContent:
    scenario = Scenario(
        id=1,
        user_id=1,
        name="Default Interview Email",
        purpose=ApplicationPurpose.INTERVIEW.value,
        document_type=DocumentType.EMAIL.value,
        system_prompt="Write a professional email.",
        is_default=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    return GeneratedContent(
        id=1,
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT.value,
        purpose=ApplicationPurpose.INTERVIEW.value,
        document_type=DocumentType.EMAIL.value,
        scenario_id=1,
        position_description="Senior ML Engineer at Acme Corp",
        subject="Application for Senior ML Engineer",
        body="Dear Hiring Manager,\n\nI am writing to apply.",
        metadata_json="{}",
        created_at=datetime.now(UTC),
        scenario=scenario,
    )


def test_build_document_pdf_returns_bytes() -> None:
    pdf_bytes = build_document_pdf(_sample_document())
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_filename_uses_purpose_and_document_type() -> None:
    document = _sample_document()
    filename = pdf_filename(document)
    assert filename == f"mailcraft-interview-email-{document.created_at:%Y%m%d}.pdf"
