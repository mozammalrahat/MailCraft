import asyncio
import logging

from google import genai
from google.genai import errors as genai_errors

from app.config import Settings
from app.services.errors import LlmError

logger = logging.getLogger(__name__)


class LlmClient:
    def __init__(
        self,
        settings: Settings,
        *,
        request_delay_seconds: float | None = None,
    ) -> None:
        self._settings = settings
        self._request_delay_seconds = (
            request_delay_seconds
            if request_delay_seconds is not None
            else settings.llm_request_delay_seconds
        )
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if not self._settings.google_api_key:
            raise LlmError("Google API key is not configured")
        if self._client is None:
            self._client = genai.Client(api_key=self._settings.google_api_key)
        return self._client

    async def generate_content(self, prompt: str, *, model: str | None = None) -> str:
        resolved_model = model or self._settings.google_judge_model
        client = self._get_client()

        try:
            response = await client.aio.models.generate_content(
                model=resolved_model,
                contents=prompt,
            )
        except genai_errors.APIError as exc:
            logger.error(
                "LLM request failed",
                extra={"model": resolved_model, "status_code": exc.code},
            )
            raise LlmError(f"LLM request failed: {exc.message}") from exc

        if self._request_delay_seconds > 0:
            logger.debug(
                "Throttling LLM request; sleeping %.1fs",
                self._request_delay_seconds,
            )
            await asyncio.sleep(self._request_delay_seconds)

        text = response.text
        if text is None:
            return ""
        return text.strip()
