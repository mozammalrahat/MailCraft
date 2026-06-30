"""Language model generation step."""

import json

from app.application.pipelines.generation_context import GenerationContext
from app.application.services.email_generation_service import (
    PROMPT_VERSION,
    build_legacy_email_prompt,
)
from app.core.exceptions import LlmError, ServiceValidationError
from app.domain.enums.generation_kind import GenerationKind
from app.schemas.application_document import StructuredApplicationDocumentOutput


class LanguageModelGenerationStep:
    """Call the language model for legacy or structured generation."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Populate model output fields on the context."""
        if context.generation_kind == GenerationKind.LEGACY_EMAIL:
            return await self._generate_legacy_email(context)
        return await self._generate_application_document(context)

    async def _generate_legacy_email(
        self, context: GenerationContext
    ) -> GenerationContext:
        """Generate a legacy intent-based email."""
        strategy_key = context.strategy.value if context.strategy else "strategy_a"
        strategy_config = context.settings.strategies.get(strategy_key)
        if strategy_config is None:
            raise ServiceValidationError(f"Unknown strategy: {strategy_key}")

        prompt = build_legacy_email_prompt(
            intent=context.intent or "",
            key_facts=context.key_facts,
            tone=context.tone.value if context.tone else "formal",
            strategy=strategy_key,
        )
        context.user_prompt = prompt
        context.prompt_version = PROMPT_VERSION
        context.model_name = strategy_config.model

        raw_output = await context.language_model_client.generate_content(
            prompt,
            model=strategy_config.model,
        )
        context.raw_language_model_output = raw_output
        return context

    async def _generate_application_document(
        self, context: GenerationContext,
    ) -> GenerationContext:
        """Generate a structured application document."""
        schema = StructuredApplicationDocumentOutput.model_json_schema()
        context.model_name = context.settings.google_model_a

        try:
            (
                parsed,
                grounding_metadata,
            ) = await context.language_model_client.generate_structured_with_grounding(
                system_instruction=context.system_instruction,
                user_prompt=context.user_prompt,
                response_schema=schema,
                model=context.settings.google_model_a,
                enable_google_search=bool(context.grounding_links),
            )
        except LlmError:
            raise
        except json.JSONDecodeError as exc:
            raise LlmError("Failed to parse structured LLM response") from exc

        context.structured_output = parsed
        context.grounding_metadata = grounding_metadata
        return context
