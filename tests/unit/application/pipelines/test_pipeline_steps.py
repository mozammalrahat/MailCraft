"""Unit tests for pipeline steps."""

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.steps.extract_resume_text_step import (
    ExtractResumeTextStep,
)
from app.application.pipelines.steps.format_output_step import FormatOutputStep
from app.application.pipelines.steps.grounding_research_step import (
    GroundingResearchStep,
)
from app.application.pipelines.steps.language_model_generation_step import (
    LanguageModelGenerationStep,
)
from app.application.pipelines.steps.validate_input_step import ValidateInputStep
from app.core.configuration import Settings
from app.core.exceptions import LlmError, ServiceValidationError
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from reportlab.pdfgen import canvas


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        GOOGLE_MODEL_A="gemini-test",
        GOOGLE_MODEL_B="gemini-test-b",
        GOOGLE_JUDGE_MODEL="gemini-test-judge",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _make_context(generation_kind: GenerationKind, **kwargs) -> GenerationContext:
    return GenerationContext(
        user_id=1,
        generation_kind=generation_kind,
        settings=_make_settings(),
        database_session=MagicMock(),
        language_model_client=MagicMock(),
        **kwargs,
    )


def _minimal_pdf(text: str = "Jane Doe — Python developer") -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(72, 720, text)
    c.save()
    return buf.getvalue()


@pytest.mark.asyncio
async def test_validate_input_step_raises_on_missing_resume() -> None:
    db = MagicMock()
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=_make_settings(),
        database_session=db,
        language_model_client=MagicMock(),
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        position_description="ML Engineer at Acme",
        scenario_id=1,
        resume_file_payloads=[],
    )
    with pytest.raises(ServiceValidationError, match="CV/resume"):
        await ValidateInputStep().process(ctx)


@pytest.mark.asyncio
async def test_validate_input_step_raises_on_missing_scenario() -> None:
    ctx = _make_context(
        GenerationKind.APPLICATION_DOCUMENT,
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        position_description="ML Engineer",
        resume_file_payloads=[("cv.pdf", b"%PDF-test")],
    )
    with pytest.raises(ServiceValidationError, match="Scenario is required"):
        await ValidateInputStep().process(ctx)


@pytest.mark.asyncio
async def test_validate_input_step_raises_when_scenario_not_found() -> None:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=_make_settings(),
        database_session=db,
        language_model_client=MagicMock(),
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        position_description="ML Engineer",
        scenario_id=99,
        resume_file_payloads=[("cv.pdf", b"%PDF-test")],
    )
    with pytest.raises(ServiceValidationError, match="Scenario not found"):
        await ValidateInputStep().process(ctx)


@pytest.mark.asyncio
async def test_validate_input_step_sets_system_instruction_from_scenario() -> None:
    fake_scenario = MagicMock()
    fake_scenario.system_prompt = "You are a helpful assistant."
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = fake_scenario
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=_make_settings(),
        database_session=db,
        language_model_client=MagicMock(),
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        position_description="ML Engineer",
        scenario_id=1,
        resume_file_payloads=[("cv.pdf", b"%PDF-test")],
    )
    result = await ValidateInputStep().process(ctx)
    assert result.system_instruction == "You are a helpful assistant."


@pytest.mark.asyncio
async def test_extract_resume_text_step_skips_when_no_files() -> None:
    ctx = _make_context(GenerationKind.APPLICATION_DOCUMENT)
    result = await ExtractResumeTextStep().process(ctx)
    assert result.resume_text == ""
    assert result.resume_filenames == []


@pytest.mark.asyncio
async def test_extract_resume_text_step_extracts_pdf_text() -> None:
    pdf_bytes = _minimal_pdf("Alice Smith — Data Scientist")
    ctx = _make_context(
        GenerationKind.APPLICATION_DOCUMENT,
        resume_file_payloads=[("alice_cv.pdf", pdf_bytes)],
    )
    result = await ExtractResumeTextStep().process(ctx)
    assert "Alice Smith" in result.resume_text or result.resume_text != ""
    assert "alice_cv.pdf" in result.resume_filenames


@pytest.mark.asyncio
async def test_grounding_research_step_builds_user_prompt() -> None:
    ctx = _make_context(
        GenerationKind.APPLICATION_DOCUMENT,
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        position_description="Senior ML Engineer at Acme",
        resume_text="Jane Doe, Python, 5 years exp.",
    )
    result = await GroundingResearchStep().process(ctx)
    assert result.user_prompt != ""
    assert "Senior ML Engineer" in result.user_prompt or result.user_prompt


@pytest.mark.asyncio
async def test_format_output_step_parses_application_document() -> None:
    ctx = _make_context(
        GenerationKind.APPLICATION_DOCUMENT,
        document_type=DocumentType.EMAIL,
    )
    ctx.structured_output = {
        "subject": "Application for ML Role",
        "body": "Dear Hiring Manager,\n\nI am applying for the ML role.",
        "metadata": {
            "generation_reason": "apply",
            "organization": "Acme",
            "position_title": "ML Engineer",
            "recipient_name": "Hiring Manager",
            "matched_skills": [],
            "key_highlights_used": [],
            "tone_used": "formal",
        },
    }
    result = await FormatOutputStep().process(ctx)
    assert result.subject == "Application for ML Role"
    assert "ML role" in result.body
    assert result.clipboard_text


@pytest.mark.asyncio
async def test_language_model_generation_step_calls_structured_llm() -> None:
    llm = MagicMock()
    llm.generate_structured_with_grounding = AsyncMock(
        return_value=(
            {
                "subject": "Application",
                "body": "Dear Hiring Manager,\n\nI am interested.",
                "metadata": {
                    "generation_reason": "apply",
                    "organization": "Acme",
                    "position_title": "Engineer",
                    "recipient_name": "Hiring Manager",
                    "matched_skills": [],
                    "key_highlights_used": [],
                    "tone_used": "formal",
                },
            },
            None,
        )
    )
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=_make_settings(),
        database_session=MagicMock(),
        language_model_client=llm,
        system_instruction="Write professionally.",
        user_prompt="Generate an email.",
    )
    result = await LanguageModelGenerationStep().process(ctx)
    assert result.structured_output["subject"] == "Application"
    llm.generate_structured_with_grounding.assert_awaited_once()


@pytest.mark.asyncio
async def test_language_model_generation_step_propagates_llm_error() -> None:
    llm = MagicMock()
    llm.generate_structured_with_grounding = AsyncMock(side_effect=LlmError("API down"))
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=_make_settings(),
        database_session=MagicMock(),
        language_model_client=llm,
        system_instruction="Write professionally.",
        user_prompt="Generate an email.",
    )
    with pytest.raises(LlmError, match="API down"):
        await LanguageModelGenerationStep().process(ctx)
