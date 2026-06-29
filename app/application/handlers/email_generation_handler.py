"""Handler for legacy email generation."""

from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.generation_pipeline import GenerationPipeline
from app.application.pipelines.steps import (
    FormatOutputStep,
    HumanizeContentStep,
    LanguageModelGenerationStep,
    PersistGeneratedContentStep,
    ValidateInputStep,
)
from app.core.configuration import Settings
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from app.schemas.email_generation import EmailGenerationRequest, EmailGenerationResponse
from sqlalchemy.orm import Session


class EmailGenerationHandler:
    """Orchestrate legacy email generation through the pipeline."""

    def __init__(self) -> None:
        self._pipeline = GenerationPipeline(
            steps=[
                ValidateInputStep(),
                LanguageModelGenerationStep(),
                FormatOutputStep(),
                HumanizeContentStep(),
                PersistGeneratedContentStep(),
            ]
        )

    async def generate_from_api(
        self,
        request: EmailGenerationRequest,
        user_id: int,
        database_session: Session,
        settings: Settings,
        language_model_client: LargeLanguageModelClient,
    ) -> EmailGenerationResponse:
        """Generate and persist a legacy email from an API request."""
        context = GenerationContext(
            user_id=user_id,
            generation_kind=GenerationKind.LEGACY_EMAIL,
            settings=settings,
            database_session=database_session,
            language_model_client=language_model_client,
            intent=request.intent,
            key_facts=request.key_facts,
            tone=request.tone,
            strategy=request.strategy,
        )
        context = await self._pipeline.run(context)
        record = context.generated_content
        response = EmailGenerationResponse(
            email=context.body,
            subject=context.subject,
            model=context.model_name or "",
            strategy=context.strategy.value if context.strategy else "",
            prompt_version=context.prompt_version or "",
            generated_content_id=record.id if record else None,
        )
        if settings.debug and context.humanization_applied:
            response.raw_email = context.raw_body
            response.raw_subject = context.raw_subject
        return response
