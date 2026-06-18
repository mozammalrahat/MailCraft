from unittest.mock import AsyncMock, MagicMock

import pytest
from app.config import Settings
from app.schemas.email import EmailGenerationRequest, EmailTone
from app.services.email.generation import generate_email
from app.services.errors import LlmError


def _sample_request() -> EmailGenerationRequest:
    return EmailGenerationRequest(
        intent="Follow up on proposal",
        key_facts=["Proposal sent on Monday", "Budget cap is $50k"],
        tone=EmailTone.FORMAL,
    )


@pytest.mark.asyncio
async def test_generate_email_returns_structured_response() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(
        return_value=(
            "Subject: Proposal Follow-Up\n\nDear team, proposal sent on Monday."
        ),
    )
    settings = Settings(google_api_key="test-key")

    result = await generate_email(_sample_request(), mock_client, settings)

    assert "Proposal Follow-Up" in result.email
    assert result.subject == "Proposal Follow-Up"
    assert result.strategy == "strategy_a"
    assert result.prompt_version == "2.0.0"
    mock_client.generate_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_email_raises_llm_error_from_client() -> None:
    mock_client = MagicMock()
    mock_client.generate_content = AsyncMock(side_effect=LlmError("API down"))
    settings = Settings(google_api_key="test-key")

    with pytest.raises(LlmError):
        await generate_email(_sample_request(), mock_client, settings)


def test_request_rejects_empty_key_facts() -> None:
    with pytest.raises(ValueError, match="non-empty key fact"):
        EmailGenerationRequest(
            intent="Test",
            key_facts=["  "],
            tone=EmailTone.CASUAL,
        )
