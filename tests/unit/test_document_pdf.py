from datetime import UTC, datetime

from app.db.models import GeneratedDocument, Scenario
from app.domain.enums.generation_kind import GenerationKind
from app.schemas.stateful import DocumentType, Purpose
from app.services.export.document_pdf import build_document_pdf, pdf_filename


def _sample_document() -> GeneratedDocument:
    scenario = Scenario(
        id=1,
        user_id=1,
        name="Default Interview Email",
        purpose=Purpose.INTERVIEW.value,
        document_type=DocumentType.EMAIL.value,
        system_prompt="test",
        is_default=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    doc = GeneratedDocument(
        id=1,
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT.value,
        scenario_id=1,
        purpose=Purpose.INTERVIEW.value,
        document_type=DocumentType.EMAIL.value,
        position_description="ML Engineer role",
        subject="Application for ML Engineer",
        body="Dear Hiring Manager,\n\nI am writing to express my interest.",
        created_at=datetime.now(UTC),
    )
    doc.scenario = scenario
    doc.document_metadata = {
        "organization": "Acme Corp",
        "position_title": "ML Engineer",
    }
    return doc


def test_build_document_pdf_returns_bytes() -> None:
    pdf_bytes = build_document_pdf(_sample_document())
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 100


def test_pdf_filename_format() -> None:
    doc = _sample_document()
    name = pdf_filename(doc)
    assert "interview" in name
    assert name.endswith(".pdf")
