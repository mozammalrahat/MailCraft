"""Persist generated content to the database."""

import json

from app.application.pipelines.generation_context import GenerationContext
from app.database.models.generated_content import GeneratedContent


class PersistGeneratedContentStep:
    """Save generation results to the database."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Insert a generated content row."""
        record = GeneratedContent(
            user_id=context.user_id,
            generation_kind=context.generation_kind.value,
            subject=context.subject,
            body=context.body,
            raw_subject=context.raw_subject,
            raw_body=context.raw_body,
            humanization_applied=context.humanization_applied,
            humanizer_model_name=(
                context.humanizer_model_name if context.humanization_applied else None
            ),
            humanizer_prompt_version=(
                context.humanizer_prompt_version
                if context.humanization_applied
                else None
            ),
            scenario_id=context.scenario_id,
            purpose=context.purpose.value if context.purpose else None,
            document_type=(
                context.document_type.value if context.document_type else None
            ),
            position_description=context.position_description,
            cv_extracted_text=context.resume_text,
            cv_filenames=context.resume_filenames,
            grounding_links=context.grounding_links,
            document_metadata=context.document_metadata,
            model_name=context.model_name,
        )
        if context.resume_storage_keys:
            record.resume_storage_keys = context.resume_storage_keys
        if context.grounding_metadata:
            record.grounding_metadata_json = json.dumps(context.grounding_metadata)

        context.database_session.add(record)
        context.database_session.commit()
        context.database_session.refresh(record)
        context.generated_content = record
        return context
