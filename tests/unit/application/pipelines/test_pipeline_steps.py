"""Unit tests for pipeline steps.

Covers ValidateInputStep, ExtractResumeTextStep, GroundingResearchStep,
FormatOutputStep, and LanguageModelGenerationStep.
"""

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
from app.domain.enums.email_strategy import EmailStrategy
from app.domain.enums.email_tone import EmailTone
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


# ---------------------------------------------------------------------------
# ValidateInputStep
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_input_step_raises_on_missing_intent() -> None:
    ctx = _make_context(GenerationKind.LEGACY_EMAIL, tone=EmailTone.FORMAL,
                        strategy=EmailStrategy.STRATEGY_A)
    with pytest.raises(ServiceValidationError, match="Intent is required"):
        await ValidateInputStep().process(ctx)


@pytest.mark.asyncio
async def test_validate_input_step_raises_on_empty_key_facts() -> None:
    ctx = _make_context(
        GenerationKind.LEGACY_EMAIL,
        intent="Test",
        tone=EmailTone.FORMAL,
        strategy=EmailStrategy.STRATEGY_A,
    )
    with pytest.raises(ServiceValidationError, match="key fact"):
        await ValidateInputStep().process(ctx)


@pytest.mark.asyncio
async def test_validate_input_step_passes_valid_legacy_email() -> None:
    ctx = _make_context(
        GenerationKind.LEGACY_EMAIL,
        intent="Test intent",
        key_facts=["Fact one"],
        tone=EmailTone.FORMAL,
        strategy=EmailStrategy.STRATEGY_A,
    )
    result = await ValidateInputStep().process(ctx)
    assert result is ctx


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


# ---------------------------------------------------------------------------
# ExtractResumeTextStep
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# GroundingResearchStep
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_grounding_research_step_skips_legacy_email() -> None:
    ctx = _make_context(GenerationKind.LEGACY_EMAIL)
    result = await GroundingResearchStep().process(ctx)
    assert result.user_prompt == ""


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


# ---------------------------------------------------------------------------
# FormatOutputStep
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_format_output_step_skips_on_validation_errors() -> None:
    ctx = _make_context(GenerationKind.LEGACY_EMAIL)
    ctx.validation_errors = ["some error"]
    result = await FormatOutputStep().process(ctx)
    assert result.body == ""


@pytest.mark.asyncio
async def test_format_output_step_parses_legacy_email_subject_and_body() -> None:
    ctx = _make_context(GenerationKind.LEGACY_EMAIL)
    ctx.raw_language_model_output = (
        "Subject: Hello World\n\nDear Test,\n\nThis is the body."
    )
    result = await FormatOutputStep().process(ctx)
    assert result.subject == "Hello World"
    assert "This is the body" in result.body
    assert result.clipboard_text != ""


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


# ---------------------------------------------------------------------------
# LanguageModelGenerationStep
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_language_model_generation_step_calls_llm_for_legacy_email() -> None:
    llm = MagicMock()
    llm.generate_content = AsyncMock(
        return_value="Subject: Test\n\nHello test email."
    )
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=_make_settings(),
        database_session=MagicMock(),
        language_model_client=llm,
        intent="Test intent",
        key_facts=["Fact one"],
        tone=EmailTone.FORMAL,
        strategy=EmailStrategy.STRATEGY_A,
    )
    result = await LanguageModelGenerationStep().process(ctx)
    assert result.raw_language_model_output == "Subject: Test\n\nHello test email."
    llm.generate_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_language_model_generation_step_raises_on_unknown_strategy() -> None:
    """Unknown strategy now raises ServiceValidationError (fail-fast)."""
    llm = MagicMock()
    llm.generate_content = AsyncMock()
    settings = _make_settings()
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=settings,
        database_session=MagicMock(),
        language_model_client=llm,
    )
    ctx.strategy = MagicMock()
    ctx.strategy.value = "nonexistent_strategy"
    with pytest.raises(ServiceValidationError):
        await LanguageModelGenerationStep().process(ctx)
    llm.generate_content.assert_not_awaited()


@pytest.mark.asyncio
async def test_language_model_generation_step_propagates_llm_error() -> None:
    llm = MagicMock()
    llm.generate_content = AsyncMock(side_effect=LlmError("API down"))
    ctx = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=_make_settings(),
        database_session=MagicMock(),
        language_model_client=llm,
        intent="Test",
        key_facts=["Fact"],
        tone=EmailTone.FORMAL,
        strategy=EmailStrategy.STRATEGY_A,
    )
    with pytest.raises(LlmError, match="API down"):
        await LanguageModelGenerationStep().process(ctx)
