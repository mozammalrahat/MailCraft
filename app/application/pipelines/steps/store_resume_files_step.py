"""Persist uploaded resume PDFs after text extraction."""

from app.application.pipelines.generation_context import GenerationContext
from app.application.services.resume_storage_service import store_resume_files


class StoreResumeFilesStep:
    """Store raw resume PDFs when configured."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Upload resume files to configured storage."""
        if not context.settings.store_uploaded_resumes:
            return context
        if not context.resume_file_payloads or context.file_storage is None:
            return context

        context.resume_storage_keys = store_resume_files(
            file_storage=context.file_storage,
            user_id=context.user_id,
            resume_file_payloads=context.resume_file_payloads,
        )
        return context
