"""Extract text from uploaded resume PDFs."""

from app.application.pipelines.generation_context import GenerationContext
from app.infrastructure.document_processing.pdf_text_extractor import (
    extract_text_from_pdfs,
)


class ExtractResumeTextStep:
    """Extract resume text from uploaded PDF files."""

    async def process(self, context: GenerationContext) -> GenerationContext:
        """Populate resume text and filenames on the context."""
        if not context.resume_file_payloads:
            return context

        resume_text, resume_filenames = extract_text_from_pdfs(
            context.resume_file_payloads,
            settings=context.settings,
        )
        context.resume_text = resume_text
        context.resume_filenames = resume_filenames
        return context
