import pytest
from app.config import Settings
from app.services.errors import LlmError
from app.services.llm.client import LlmClient


@pytest.mark.asyncio
async def test_generate_content_raises_without_api_key() -> None:
    client = LlmClient(Settings(google_api_key=""))

    with pytest.raises(LlmError, match="API key"):
        await client.generate_content("test prompt")
