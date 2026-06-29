"""Validate generation inputs."""

from app.application.pipelines.generation_context import GenerationContext
from app.database.models.scenario import Scenario
from app.domain.enums.generation_kind import GenerationKind


class ValidateInputStep:
    """Validate inputs before generation."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Validate context fields for the selected generation kind."""
        if context.generation_kind == GenerationKind.LEGACY_EMAIL:
            if not context.intent or not context.intent.strip():
                context.validation_errors.append("Intent is required")
            if not context.key_facts:
                context.validation_errors.append("At least one key fact is required")
            if context.tone is None:
                context.validation_errors.append("Tone is required")
            if context.strategy is None:
                context.validation_errors.append("Strategy is required")
            return context

        if context.purpose is None or context.document_type is None:
            context.validation_errors.append("Purpose and document type are required")
        if not context.position_description or not context.position_description.strip():
            context.validation_errors.append("Position description is required")
        if not context.resume_file_payloads:
            context.validation_errors.append("At least one CV/resume PDF is required")
        if context.scenario_id is None:
            context.validation_errors.append("Scenario is required")
            return context

        scenario = (
            context.database_session.query(Scenario)
            .filter(
                Scenario.id == context.scenario_id,
                Scenario.user_id == context.user_id,
            )
            .first()
        )
        if scenario is None:
            context.validation_errors.append("Scenario not found")
        else:
            context.system_instruction = scenario.system_prompt

        return context
