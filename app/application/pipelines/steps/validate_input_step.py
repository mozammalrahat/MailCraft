"""Validate generation inputs."""

from app.application.pipelines.generation_context import GenerationContext
from app.core.exceptions import ServiceValidationError
from app.database.models.scenario import Scenario
from app.domain.enums.generation_kind import GenerationKind


class ValidateInputStep:
    """Validate inputs before generation, raising on first failure."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Validate context fields for the selected generation kind."""
        if context.generation_kind == GenerationKind.LEGACY_EMAIL:
            if not context.intent or not context.intent.strip():
                raise ServiceValidationError("Intent is required")
            if not context.key_facts:
                raise ServiceValidationError("At least one key fact is required")
            if context.tone is None:
                raise ServiceValidationError("Tone is required")
            if context.strategy is None:
                raise ServiceValidationError("Strategy is required")
            return context

        if context.purpose is None or context.document_type is None:
            raise ServiceValidationError("Purpose and document type are required")
        if not context.position_description or not context.position_description.strip():
            raise ServiceValidationError("Position description is required")
        if not context.resume_file_payloads:
            raise ServiceValidationError("At least one CV/resume PDF is required")
        if context.scenario_id is None:
            raise ServiceValidationError("Scenario is required")

        scenario = (
            context.database_session.query(Scenario)
            .filter(
                Scenario.id == context.scenario_id,
                Scenario.user_id == context.user_id,
            )
            .first()
        )
        if scenario is None:
            raise ServiceValidationError("Scenario not found")

        context.system_instruction = scenario.system_prompt
        return context
