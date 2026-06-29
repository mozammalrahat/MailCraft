"""Backward-compatible email generation service."""

from app.application.handlers.email_generation_handler import EmailGenerationHandler
from app.core.configuration import Settings
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.schemas.email_generation import EmailGenerationRequest, EmailGenerationResponse

_email_handler = EmailGenerationHandler()


async def generate_email(
    request: EmailGenerationRequest,
    language_model_client: LargeLanguageModelClient,
    settings: Settings,
    *,
    user_id: int | None = None,
    database_session=None,
) -> EmailGenerationResponse:
    """Generate email without persistence when user_id is omitted."""
    if user_id is not None and database_session is not None:
        return await _email_handler.generate_from_api(
            request=request,
            user_id=user_id,
            database_session=database_session,
            settings=settings,
            language_model_client=language_model_client,
        )

    # Evaluation pipeline: generate without DB persistence
    from app.application.pipelines.generation_context import GenerationContext
    from app.application.pipelines.generation_pipeline import GenerationPipeline
    from app.application.pipelines.steps import (
        FormatOutputStep,
        LanguageModelGenerationStep,
        ValidateInputStep,
    )
    from app.domain.enums.generation_kind import GenerationKind

    pipeline = GenerationPipeline(
        steps=[ValidateInputStep(), LanguageModelGenerationStep(), FormatOutputStep()]
    )
    context = GenerationContext(
        user_id=0,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=settings,
        database_session=database_session,
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
