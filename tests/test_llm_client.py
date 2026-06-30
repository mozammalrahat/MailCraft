from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.configuration import Settings
from app.core.exceptions import LlmError
from app.infrastructure.large_language_model.client import (
    LargeLanguageModelClient,
    _parse_json_text,
)
from google.genai import errors as genai_errors


@pytest.mark.asyncio
async def test_generate_content_raises_without_api_key() -> None:
    client = LargeLanguageModelClient(Settings(google_api_key=""))

    with pytest.raises(LlmError, match="API key"):
        await client.generate_content("test prompt")


@pytest.mark.asyncio
async def test_generate_content_applies_request_delay() -> None:
    settings = Settings(google_api_key="test-key", GOOGLE_MODEL_A="gemini-test")
    client = LargeLanguageModelClient(settings, request_delay_seconds=0.05)

    mock_response = MagicMock()
    mock_response.text = "generated"

    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(return_value=mock_response)

    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with (
        patch.object(client, "_get_client", return_value=mock_genai_client),
        patch(
            "app.infrastructure.large_language_model.client.asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep_mock,
    ):
        result = await client.generate_content("test prompt")

    assert result == "generated"
    sleep_mock.assert_awaited_once_with(0.05)


@pytest.mark.asyncio
async def test_structured_without_search_uses_single_json_call() -> None:
    settings = Settings(google_api_key="test-key", GOOGLE_MODEL_A="gemini-test")
    client = LargeLanguageModelClient(settings, request_delay_seconds=0)

    structured_response = MagicMock()
    structured_response.text = '{"subject":"Hi","body":"Hello","metadata":{}}'

    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(return_value=structured_response)
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with patch.object(client, "_get_client", return_value=mock_genai_client):
        parsed, grounding = await client.generate_structured_with_grounding(
            system_instruction="system",
            user_prompt="user",
            response_schema={"type": "object"},
            enable_google_search=False,
        )

    assert parsed["subject"] == "Hi"
    assert grounding is None
    assert mock_aio.models.generate_content.await_count == 1
    call_kwargs = mock_aio.models.generate_content.await_args.kwargs
    assert call_kwargs["config"].response_mime_type == "application/json"
    assert call_kwargs["config"].tools is None


@pytest.mark.asyncio
async def test_structured_with_search_uses_two_phase_calls() -> None:
    settings = Settings(google_api_key="test-key", GOOGLE_MODEL_A="gemini-test")
    client = LargeLanguageModelClient(settings, request_delay_seconds=0)

    research_response = MagicMock()
    research_response.text = "Acme Corp builds ML platforms."
    research_response.candidates = [MagicMock(grounding_metadata=None)]

    structured_response = MagicMock()
    structured_response.text = '{"subject":"Hi","body":"Hello","metadata":{}}'

    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(
        side_effect=[research_response, structured_response]
    )
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with patch.object(client, "_get_client", return_value=mock_genai_client):
        parsed, grounding = await client.generate_structured_with_grounding(
            system_instruction="system",
            user_prompt="user",
            response_schema={"type": "object"},
            enable_google_search=True,
        )

    assert parsed["body"] == "Hello"
    assert mock_aio.models.generate_content.await_count == 2

    research_kwargs = mock_aio.models.generate_content.await_args_list[0].kwargs
    structured_kwargs = mock_aio.models.generate_content.await_args_list[1].kwargs

    assert research_kwargs["config"].tools is not None
    assert research_kwargs["config"].response_mime_type is None

    assert structured_kwargs["config"].tools is None
    assert structured_kwargs["config"].response_mime_type == "application/json"
    assert "Acme Corp builds ML platforms." in structured_kwargs["contents"]


def test_parse_json_text_strips_markdown_fence() -> None:
    parsed = _parse_json_text('```json\n{"subject":"Hi","body":"Hello"}\n```')
    assert parsed["subject"] == "Hi"


@pytest.mark.asyncio
async def test_generate_content_retries_transient_error() -> None:
    settings = Settings(
        google_api_key="test-key",
        GOOGLE_MODEL_A="gemini-test",
        llm_max_retries=3,
        llm_retry_base_delay_seconds=0.0,
    )
    client = LargeLanguageModelClient(settings, request_delay_seconds=0)

    mock_response = MagicMock()
    mock_response.text = "generated"

    transient_error = genai_errors.APIError(429, {"message": "rate limited"})
    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(
        side_effect=[transient_error, mock_response]
    )
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with patch.object(client, "_get_client", return_value=mock_genai_client):
        result = await client.generate_content("test prompt")

    assert result == "generated"
    assert mock_aio.models.generate_content.await_count == 2


@pytest.mark.asyncio
async def test_generate_content_does_not_retry_client_error() -> None:
    settings = Settings(
        google_api_key="test-key",
        GOOGLE_MODEL_A="gemini-test",
        llm_max_retries=3,
        llm_retry_base_delay_seconds=0.0,
    )
    client = LargeLanguageModelClient(settings, request_delay_seconds=0)

    client_error = genai_errors.APIError(400, {"message": "bad request"})
    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(side_effect=client_error)
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with patch.object(client, "_get_client", return_value=mock_genai_client):
        with pytest.raises(LlmError, match="LLM request failed"):
            await client.generate_content("test prompt")

    assert mock_aio.models.generate_content.await_count == 1


@pytest.mark.asyncio
async def test_generate_content_logs_latency() -> None:
    settings = Settings(
        google_api_key="test-key",
        GOOGLE_MODEL_A="gemini-test",
        llm_max_retries=1,
    )
    client = LargeLanguageModelClient(settings, request_delay_seconds=0)

    mock_response = MagicMock()
    mock_response.text = "generated"
    mock_aio = MagicMock()
    mock_aio.models.generate_content = AsyncMock(return_value=mock_response)
    mock_genai_client = MagicMock()
    mock_genai_client.aio = mock_aio

    with (
        patch.object(client, "_get_client", return_value=mock_genai_client),
        patch(
            "app.infrastructure.large_language_model.client.logger.info"
        ) as info_mock,
    ):
        await client.generate_content("test prompt")

    info_mock.assert_called()
    assert info_mock.call_args.args[0] == "LLM call completed"
    assert info_mock.call_args.kwargs["extra"]["operation"] == "generate_content"
    assert info_mock.call_args.kwargs["extra"]["success"] is True
