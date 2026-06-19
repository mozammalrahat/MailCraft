from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.config import Settings
from app.services.errors import LlmError
from app.services.llm.client import LlmClient


@pytest.mark.asyncio
async def test_generate_content_raises_without_api_key() -> None:
    client = LlmClient(Settings(google_api_key=""))

    with pytest.raises(LlmError, match="API key"):
        await client.generate_content("test prompt")


@pytest.mark.asyncio
async def test_generate_content_applies_request_delay() -> None:
    settings = Settings(google_api_key="test-key", GOOGLE_JUDGE_MODEL="gemini-test")
    client = LlmClient(settings, request_delay_seconds=0.05)

    mock_response = MagicMock()
    mock_response.text = "generated"

    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(return_value=mock_response)

    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with (
        patch.object(client, "_get_client", return_value=mock_genai_client),
        patch(
            "app.services.llm.client.asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep_mock,
    ):
        result = await client.generate_content("test prompt")

    assert result == "generated"
    sleep_mock.assert_awaited_once_with(0.05)
