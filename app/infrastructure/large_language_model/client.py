import asyncio
import json
import logging
import re

from app.core.configuration import Settings
from app.services.errors import LlmError
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

logger = logging.getLogger(__name__)

_JSON_FENCE_PATTERN = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
    re.DOTALL | re.IGNORECASE,
)


class LargeLanguageModelClient:
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

    async def _apply_request_delay(self) -> None:
        if self._request_delay_seconds > 0:
            logger.debug(
                "Throttling LLM request; sleeping %.1fs",
                self._request_delay_seconds,
            )
            await asyncio.sleep(self._request_delay_seconds)

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

        await self._apply_request_delay()

        text = response.text
        if text is None:
            return ""
        return text.strip()

    async def generate_structured_with_grounding(
        self,
        *,
        system_instruction: str,
        user_prompt: str,
        response_schema: dict,
        model: str | None = None,
        enable_google_search: bool = True,
    ) -> tuple[dict, dict | None]:
        """Generate structured JSON, optionally enriched with Google Search.

        Gemini 2.5 does not allow ``tools`` and ``response_mime_type=application/json``
        in the same request. When search is enabled we run a grounding pass first,
        then a separate structured JSON pass without tools.
        """
        resolved_model = model or self._settings.google_model_a
        grounding_metadata: dict | None = None
        research_context = ""

        if enable_google_search:
            research_response, grounding_metadata = await self._run_grounding_research(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                model=resolved_model,
            )
            research_context = (research_response.text or "").strip()

        structured_prompt = user_prompt
        if research_context:
            structured_prompt = (
                f"{user_prompt}\n\n"
                "--- Web research context (use to personalize; do not invent facts "
                "beyond this, the CV, and the position description) ---\n"
                f"{research_context}"
            )

        parsed = await self._run_structured_generation(
            system_instruction=system_instruction,
            user_prompt=structured_prompt,
            response_schema=response_schema,
            model=resolved_model,
        )
        return parsed, grounding_metadata

    async def _run_grounding_research(
        self,
        *,
        system_instruction: str,
        user_prompt: str,
        model: str,
    ) -> tuple[object, dict | None]:
        client = self._get_client()
        research_prompt = (
            "Use Google Search to research the organizations, labs, professors, and "
            "roles referenced below. Summarize only factual findings useful for writing "
            "a tailored application email or cover letter. Do not draft the email yet.\n\n"
            f"{user_prompt}"
        )
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )

        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=research_prompt,
                config=config,
            )
        except genai_errors.APIError as exc:
            logger.error(
                "Grounding research request failed",
                extra={"model": model, "status_code": exc.code},
            )
            raise LlmError(f"LLM request failed: {exc.message}") from exc

        await self._apply_request_delay()
        return response, _extract_grounding_metadata(response)

    async def _run_structured_generation(
        self,
        *,
        system_instruction: str,
        user_prompt: str,
        response_schema: dict,
        model: str,
    ) -> dict:
        client = self._get_client()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_json_schema=response_schema,
        )

        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config,
            )
        except genai_errors.APIError as exc:
            logger.error(
                "Structured LLM request failed",
                extra={"model": model, "status_code": exc.code},
            )
            raise LlmError(f"LLM request failed: {exc.message}") from exc

        await self._apply_request_delay()

        raw_text = response.text or "{}"
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return _parse_json_text(raw_text)


def _extract_grounding_metadata(response: object) -> dict | None:
    candidates = getattr(response, "candidates", None)
    if not candidates:
        return None

    grounding = getattr(candidates[0], "grounding_metadata", None)
    if grounding is None:
        return None

    metadata: dict[str, object] = {}
    web_search_queries = getattr(grounding, "web_search_queries", None)
    if web_search_queries:
        metadata["web_search_queries"] = list(web_search_queries)

    grounding_chunks = getattr(grounding, "grounding_chunks", None)
    if grounding_chunks:
        citations: list[dict[str, str]] = []
        for chunk in grounding_chunks:
            web = getattr(chunk, "web", None)
            if web is None:
                continue
            citations.append(
                {
                    "title": getattr(web, "title", "") or "",
                    "uri": getattr(web, "uri", "") or "",
                }
            )
        if citations:
            metadata["citations"] = citations

    return metadata or None


def _parse_json_text(raw_text: str) -> dict:
    text = raw_text.strip()
    fence_match = _JSON_FENCE_PATTERN.match(text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LlmError("Failed to parse structured LLM response") from exc


# Backward-compatible alias used by existing tests and imports.
LlmClient = LargeLanguageModelClient
