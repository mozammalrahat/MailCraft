from unittest.mock import AsyncMock, MagicMock

import pytest
from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.steps.humanize_content_step import HumanizeContentStep
from app.core.configuration import Settings
from app.core.exceptions import LlmError
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind


def _app_doc_context(**overrides) -> GenerationContext:
    context = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=Settings(
            google_api_key="test-key",
            GOOGLE_MODEL_A="gemini-test",
            humanize_content_enabled=True,
        ),
        database_session=MagicMock(),
        language_model_client=MagicMock(),
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        scenario_id=1,
        position_description="ML Engineer",
        document_metadata={
            "tone_used": "formal",
            "key_highlights_used": ["Demo on Tuesday", "Pricing for 50 seats"],
            "matched_skills": [],
        },
    )
    for key, value in overrides.items():
        setattr(context, key, value)
    return context


@pytest.mark.asyncio
async def test_humanize_content_step_preserves_raw_and_updates_body() -> None:
    language_model_client = MagicMock()
    language_model_client.generate_content = AsyncMock(
        return_value=(
            "Subject: Quick follow-up\n\n"
            "Hi Alex,\n\nFollow up after demo. Demo on Tuesday went well. "
            "Pricing for 50 seats is attached."
        )
    )

    context = _app_doc_context(language_model_client=language_model_client)
    context.subject = "Follow-Up Regarding Product Demonstration"
    context.body = (
        "Dear Recipient,\n\n"
        "Furthermore, I am writing to delve into the pivotal outcomes "
        "from our recent demonstration on Tuesday. Pricing for 50 seats is attached."
    )

    result = await HumanizeContentStep().process(context)

    assert result.raw_subject == "Follow-Up Regarding Product Demonstration"
    assert "Furthermore" in result.raw_body
    assert result.subject == "Quick follow-up"
    assert "Hi Alex" in result.body
    assert result.humanization_applied is True
    assert result.humanizer_model_name == "gemini-test"
    assert result.humanizer_prompt_version == "1.1.0"
    language_model_client.generate_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_humanize_content_step_skips_when_disabled() -> None:
    language_model_client = MagicMock()
    language_model_client.generate_content = AsyncMock()

    context = _app_doc_context(
        settings=Settings(
            google_api_key="test-key",
            GOOGLE_MODEL_A="gemini-test",
            humanize_content_enabled=False,
        ),
        language_model_client=language_model_client,
    )
    context.body = "Original body"

    result = await HumanizeContentStep().process(context)

    assert result.body == "Original body"
    assert result.raw_body is None
    assert result.humanization_applied is False
    language_model_client.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_humanize_content_step_fallback_on_llm_error() -> None:
    language_model_client = MagicMock()
    language_model_client.generate_content = AsyncMock(
        side_effect=LlmError("API unavailable")
    )

    context = _app_doc_context(language_model_client=language_model_client)
    context.subject = "Original subject"
    context.body = "Original body with Demo on Tuesday."

    result = await HumanizeContentStep().process(context)

    assert result.subject == "Original subject"
    assert result.body == "Original body with Demo on Tuesday."
    assert result.humanization_applied is False
    assert result.humanizer_model_name is None


@pytest.mark.asyncio
async def test_humanize_content_step_fallback_when_facts_dropped() -> None:
    language_model_client = MagicMock()
    language_model_client.generate_content = AsyncMock(
        return_value=(
            "Subject: Quick follow-up\n\n"
            "Hi Alex,\n\nThanks again for the conversation."
        )
    )

    context = _app_doc_context(language_model_client=language_model_client)
    context.subject = "Follow-Up Regarding Product Demonstration"
    context.body = (
        "Dear Recipient,\n\n"
        "Demo on Tuesday went well. Pricing for 50 seats is attached."
    )

    result = await HumanizeContentStep().process(context)

    assert result.subject == "Follow-Up Regarding Product Demonstration"
    assert "Pricing for 50 seats" in result.body
    assert result.humanization_applied is False
