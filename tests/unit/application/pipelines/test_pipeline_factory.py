"""Factory helpers for generation pipeline tests."""

from app.application.pipelines.pipeline_factory import (
    build_application_document_pipeline,
)
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


def test_build_application_document_pipeline_includes_all_steps() -> None:
    pipeline = build_application_document_pipeline()

    step_types = [type(step) for step in pipeline._steps]
    assert step_types == [
        ValidateInputStep,
        ExtractResumeTextStep,
        StoreResumeFilesStep,
        GroundingResearchStep,
        LanguageModelGenerationStep,
        FormatOutputStep,
        HumanizeContentStep,
        PersistGeneratedContentStep,
    ]
