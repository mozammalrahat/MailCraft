"""Language model generation step."""

import json

from app.application.pipelines.generation_context import GenerationContext
from app.core.exceptions import LlmError
from app.schemas.application_document import StructuredApplicationDocumentOutput


class LanguageModelGenerationStep:
    """Call the language model for structured application document generation."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Populate model output fields on the context."""
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
