"""Persist generated content to the database."""

import json

from app.application.pipelines.generation_context import GenerationContext
from app.database.models.generated_content import GeneratedContent
from app.domain.enums.generation_kind import GenerationKind
from app.services.errors import ServiceValidationError


class PersistGeneratedContentStep:
    """Save generation results to the database."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Insert a generated content row."""
        if context.validation_errors:
            raise ServiceValidationError(context.validation_errors[0])

        record = GeneratedContent(
            user_id=context.user_id,
            generation_kind=context.generation_kind.value,
            subject=context.subject,
            body=context.body,
            raw_subject=context.raw_subject,
            raw_body=context.raw_body,
            humanization_applied=context.humanization_applied,
        )

        if context.generation_kind == GenerationKind.LEGACY_EMAIL:
            record.intent = context.intent
            record.key_facts = context.key_facts
            record.tone = context.tone.value if context.tone else None
            record.strategy = context.strategy.value if context.strategy else None
            record.model_name = context.model_name
            record.prompt_version = context.prompt_version
        else:
            record.scenario_id = context.scenario_id
            record.purpose = context.purpose.value if context.purpose else None
            record.document_type = (
                context.document_type.value if context.document_type else None
            )
            record.position_description = context.position_description
            record.cv_extracted_text = context.resume_text
            record.cv_filenames = context.resume_filenames
            record.grounding_links = context.grounding_links
            record.document_metadata = context.document_metadata
            record.model_name = context.model_name
            if context.grounding_metadata:
                record.grounding_metadata_json = json.dumps(context.grounding_metadata)

        context.database_session.add(record)
        context.database_session.commit()
        context.database_session.refresh(record)
        context.generated_content = record
        return context
