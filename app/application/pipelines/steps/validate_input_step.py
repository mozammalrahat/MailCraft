"""Validate generation inputs."""

from app.application.pipelines.generation_context import GenerationContext
from app.core.exceptions import ServiceValidationError
from app.database.models.scenario import Scenario


class ValidateInputStep:
    """Validate inputs before generation, raising on first failure."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Validate context fields for application document generation."""
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
