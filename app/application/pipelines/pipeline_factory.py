"""Factory helpers for generation pipelines."""

from app.application.pipelines.generation_pipeline import GenerationPipeline
from app.application.pipelines.steps import (
    ExtractResumeTextStep,
    FormatOutputStep,
    GroundingResearchStep,
    HumanizeContentStep,
    LanguageModelGenerationStep,
    PersistGeneratedContentStep,
    StoreResumeFilesStep,
    ValidateInputStep,
)


def build_application_document_pipeline() -> GenerationPipeline:
    """Build the application document pipeline (always persists)."""
    return GenerationPipeline(
        steps=[
            ValidateInputStep(),
            ExtractResumeTextStep(),
            StoreResumeFilesStep(),
            GroundingResearchStep(),
            LanguageModelGenerationStep(),
            FormatOutputStep(),
            HumanizeContentStep(),
            PersistGeneratedContentStep(),
        ]
    )
