"""Optional grounding research step."""

from app.application.pipelines.generation_context import GenerationContext
from app.domain.enums.generation_kind import GenerationKind
from app.prompts.builders.application_document_user_prompt_builder import (
    build_application_document_user_prompt,
)


class GroundingResearchStep:
    """Build application document user prompt."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Build user prompt for application documents."""
        if context.generation_kind != GenerationKind.APPLICATION_DOCUMENT:
            return context
        if context.purpose is None or context.document_type is None:
            return context

        context.user_prompt = build_application_document_user_prompt(
            purpose=context.purpose,
            document_type=context.document_type,
            position_description=context.position_description or "",
            resume_text=context.resume_text,
            grounding_links=context.grounding_links,
        )
        return context
