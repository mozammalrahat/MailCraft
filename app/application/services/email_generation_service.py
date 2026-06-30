"""Legacy email generation helpers."""

import re

from app.core.configuration import Settings
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.prompts.builders import PROMPT_BUILDERS
from app.schemas.email_generation import EmailGenerationRequest, EmailGenerationResponse
from sqlalchemy.orm import Session

PROMPT_VERSION = "2.0.0"

SUPPORTED_STRATEGIES = frozenset(PROMPT_BUILDERS.keys())

_SUBJECT_PATTERN = re.compile(r"^Subject:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def build_legacy_email_prompt(
    intent: str,
    key_facts: list[str],
    tone: str,
    strategy: str,
) -> str:
    """Build a legacy email prompt for the given strategy."""
    builder = PROMPT_BUILDERS.get(strategy)
    if builder is None:
        message = f"Unsupported strategy: {strategy}"
        raise ValueError(message)
    return builder(intent, key_facts, tone)


def parse_legacy_email_output(raw_output: str) -> tuple[str | None, str]:
    """Parse subject and body from raw legacy email output."""
    match = _SUBJECT_PATTERN.search(raw_output)
    if not match:
        return None, raw_output.strip()

    subject = match.group(1).strip()
    body = raw_output[match.end() :].strip()
    return subject, body


def build_prompt(request: EmailGenerationRequest, strategy: str = "strategy_a") -> str:
    """Build a legacy email prompt for the given strategy."""
    builder = PROMPT_BUILDERS.get(strategy)
    if builder is None:
        message = f"Unsupported strategy: {strategy}"
        raise ValueError(message)
    return builder(
        request.intent,
        request.key_facts,
        request.tone.value,
    )


def get_prompt_version() -> str:
    """Return the legacy email prompt version."""
    return PROMPT_VERSION


async def generate_email_without_persistence(
    request: EmailGenerationRequest,
    language_model_client: LargeLanguageModelClient,
    settings: Settings,
) -> EmailGenerationResponse:
    """Generate email without persistence for offline evaluation."""
    from app.application.pipelines.generation_context import GenerationContext
    from app.application.pipelines.pipeline_factory import build_legacy_email_pipeline
    from app.domain.enums.generation_kind import GenerationKind

    pipeline = build_legacy_email_pipeline(include_persist=False)
    context = GenerationContext(
        user_id=0,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=settings,
        database_session=None,
        language_model_client=language_model_client,
        intent=request.intent,
        key_facts=request.key_facts,
        tone=request.tone,
        strategy=request.strategy,
    )
    context = await pipeline.run(context)
    return EmailGenerationResponse(
        email=context.body,
        subject=context.subject,
        model=context.model_name or "",
        strategy=context.strategy.value if context.strategy else "",
        prompt_version=context.prompt_version or "",
    )


async def generate_email(
    request: EmailGenerationRequest,
    language_model_client: LargeLanguageModelClient,
    settings: Settings,
    *,
    user_id: int | None = None,
    database_session: Session | None = None,
) -> EmailGenerationResponse:
    """Generate email with optional persistence."""
    if user_id is not None and database_session is not None:
        from app.application.handlers.email_generation_handler import (
            EmailGenerationHandler,
        )

        handler = EmailGenerationHandler()
        return await handler.generate_from_api(
            request=request,
            user_id=user_id,
            database_session=database_session,
            settings=settings,
            language_model_client=language_model_client,
        )
    return await generate_email_without_persistence(
        request=request,
        language_model_client=language_model_client,
        settings=settings,
    )
