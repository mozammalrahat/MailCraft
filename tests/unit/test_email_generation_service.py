from unittest.mock import AsyncMock, MagicMock

import pytest
from app.application.services.email_generation_service import (
    generate_email,
    generate_email_without_persistence,
)
from app.core.configuration import Settings
from app.core.exceptions import LlmError
from app.schemas.email import EmailGenerationRequest, EmailTone


def _sample_request() -> EmailGenerationRequest:
    return EmailGenerationRequest(
        intent="Follow up on proposal",
        key_facts=["Proposal sent on Monday", "Budget cap is $50k"],
        tone=EmailTone.FORMAL,
    )


def _settings(*, humanize: bool = False) -> Settings:
    return Settings(
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
        humanize_content_enabled=humanize,
    )


@pytest.mark.asyncio
async def test_generate_email_returns_structured_response() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        return_value=(
            "Subject: Follow up on proposal\n\n"
            "Dear Alex,\n\nChecking in on the proposal."
        )
    )

    result = await generate_email(
        _sample_request(),
        mock_client,
        _settings(),
    )

    assert "Dear Alex" in result.email
    assert result.subject == "Follow up on proposal"
    assert result.strategy == "strategy_a"


@pytest.mark.asyncio
async def test_generate_email_without_persistence_runs_humanizer_when_enabled() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        side_effect=[
            (
                "Subject: Follow up on proposal\n\n"
                "Dear Alex,\n\nFurthermore, I am writing to delve into the proposal."
            ),
            (
                "Subject: Quick follow-up\n\n"
                "Hi Alex,\n\nFollow up on proposal. Proposal sent on Monday. "
                "Budget cap is $50k."
            ),
        ]
    )

    result = await generate_email_without_persistence(
        _sample_request(),
        mock_client,
        _settings(humanize=True),
    )

    assert result.subject == "Quick follow-up"
    assert "Hi Alex" in result.email
    assert mock_client.generate_content.await_count == 2


@pytest.mark.asyncio
async def test_generate_email_raises_llm_error_on_failure() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(side_effect=LlmError("API unavailable"))

    with pytest.raises(LlmError, match="API unavailable"):
        await generate_email(_sample_request(), mock_client, _settings())
