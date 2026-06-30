from app.application.pipelines.pipeline_factory import build_legacy_email_pipeline
from app.application.pipelines.steps import (
    FormatOutputStep,
    HumanizeContentStep,
    LanguageModelGenerationStep,
    PersistGeneratedContentStep,
    ValidateInputStep,
)


def test_build_legacy_email_pipeline_includes_humanizer_without_persist() -> None:
    pipeline = build_legacy_email_pipeline(include_persist=False)

    step_types = [type(step) for step in pipeline._steps]
    assert step_types == [
        ValidateInputStep,
        LanguageModelGenerationStep,
        FormatOutputStep,
        HumanizeContentStep,
    ]


def test_build_legacy_email_pipeline_includes_persist_when_requested() -> None:
    pipeline = build_legacy_email_pipeline(include_persist=True)

    step_types = [type(step) for step in pipeline._steps]
    assert step_types[-1] is PersistGeneratedContentStep
