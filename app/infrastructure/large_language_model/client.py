import asyncio
import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.configuration import Settings
from app.core.exceptions import LlmError
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

logger = logging.getLogger(__name__)

_JSON_FENCE_PATTERN = re.compile(
    r"^```(?:json)?\s*\n?(.*?)\n?```\s*$",
    re.DOTALL | re.IGNORECASE,
)
_RETRYABLE_STATUS_CODES = {429, 500, 503}
T = TypeVar("T")


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

    async def _execute_with_retry(
        self,
        operation: str,
        model: str,
        call: Callable[[], Awaitable[T]],
    ) -> T:
        """Run an LLM call with exponential backoff on transient API errors."""
        max_retries = self._settings.llm_max_retries
        base_delay = self._settings.llm_retry_base_delay_seconds
        max_delay = self._settings.llm_retry_max_delay_seconds

        for attempt in range(1, max_retries + 1):
            start = time.perf_counter()
            try:
                result = await call()
            except genai_errors.APIError as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000)
                retryable = exc.code in _RETRYABLE_STATUS_CODES
                is_final_attempt = attempt >= max_retries

                logger.info(
                    "LLM call completed",
                    extra={
                        "operation": operation,
                        "model": model,
                        "latency_ms": elapsed_ms,
                        "attempt": attempt,
                        "success": False,
                        "status_code": exc.code,
                    },
                )

                if not retryable or is_final_attempt:
                    raise LlmError(f"LLM request failed: {exc.message}") from exc

                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logger.warning(
                    "Retrying LLM call after transient failure",
                    extra={
                        "operation": operation,
                        "model": model,
                        "status_code": exc.code,
                        "attempt": attempt,
                        "retry_delay_seconds": delay,
                    },
                )
                await asyncio.sleep(delay)
                continue

            elapsed_ms = round((time.perf_counter() - start) * 1000)
            logger.info(
                "LLM call completed",
                extra={
                    "operation": operation,
                    "model": model,
                    "latency_ms": elapsed_ms,
                    "attempt": attempt,
                    "success": True,
                },
            )
            return result

        raise LlmError("LLM request failed after retries")

    async def generate_content(self, prompt: str, *, model: str | None = None) -> str:
        resolved_model = model or self._settings.google_judge_model

        async def _call() -> str:
            client = self._get_client()
            response = await client.aio.models.generate_content(
                model=resolved_model,
                contents=prompt,
            )
            _log_token_usage(
                response, operation="generate_content", model=resolved_model
            )
            text = response.text
            if text is None:
                return ""
            return text.strip()

        result = await self._execute_with_retry(
            "generate_content",
            resolved_model,
            _call,
        )
        await self._apply_request_delay()
        return result

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
        research_prompt = (
            "Use Google Search to research the organizations, labs, professors, "
            "and roles referenced below. Summarize only factual findings useful "
            "for writing a tailored application email or cover letter. "
            "Do not draft the email yet.\n\n"
            f"{user_prompt}"
        )
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        )

        async def _call() -> object:
            client = self._get_client()
            resp = await client.aio.models.generate_content(
                model=model,
                contents=research_prompt,
                config=config,
            )
            _log_token_usage(resp, operation="grounding", model=model)
            return resp

        response = await self._execute_with_retry("grounding", model, _call)
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
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_json_schema=response_schema,
        )

        async def _call() -> dict:
            client = self._get_client()
            response = await client.aio.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config,
            )
            _log_token_usage(response, operation="structured", model=model)
            raw_text = response.text or "{}"
            try:
                return json.loads(raw_text)
            except json.JSONDecodeError:
                return _parse_json_text(raw_text)

        parsed = await self._execute_with_retry("structured", model, _call)
        await self._apply_request_delay()
        return parsed


def _log_token_usage(response: object, *, operation: str, model: str) -> None:
    """Log Gemini token usage from a response object when available."""
    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return
    logger.info(
        "LLM token usage",
        extra={
            "operation": operation,
            "model": model,
            "prompt_tokens": getattr(usage, "prompt_token_count", None),
            "candidates_tokens": getattr(usage, "candidates_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
        },
    )


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
