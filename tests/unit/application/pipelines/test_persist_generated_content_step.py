from unittest.mock import MagicMock

import pytest
from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.steps.persist_generated_content_step import (
    PersistGeneratedContentStep,
)
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from tests.support.settings_factory import build_test_settings


@pytest.mark.asyncio
async def test_persist_generated_content_stores_humanizer_metadata() -> None:
    database_session = MagicMock()
    context = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=build_test_settings(),
        database_session=database_session,
        language_model_client=MagicMock(),
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        scenario_id=1,
        position_description="ML Engineer",
    )
    context.subject = "Humanized subject"
    context.body = "Humanized body"
    context.raw_subject = "Raw subject"
    context.raw_body = "Raw body"
    context.humanization_applied = True
    context.humanizer_model_name = "gemini-humanizer"
    context.humanizer_prompt_version = "1.1.0"
    context.model_name = "gemini-test"
    context.document_metadata = {"tone_used": "formal"}

    await PersistGeneratedContentStep().process(context)

    record = database_session.add.call_args.args[0]
    assert record.humanizer_model_name == "gemini-humanizer"
    assert record.humanizer_prompt_version == "1.1.0"
    assert record.purpose == ApplicationPurpose.INTERVIEW.value


@pytest.mark.asyncio
async def test_persist_generated_content_omits_humanizer_metadata_on_fallback() -> None:
    database_session = MagicMock()
    context = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=build_test_settings(),
        database_session=database_session,
        language_model_client=MagicMock(),
        purpose=ApplicationPurpose.INTERVIEW,
        document_type=DocumentType.EMAIL,
        scenario_id=1,
        position_description="ML Engineer",
    )
    context.subject = "Raw subject"
    context.body = "Raw body"
    context.humanization_applied = False
    context.humanizer_model_name = None
    context.humanizer_prompt_version = None
    context.model_name = "gemini-test"

    await PersistGeneratedContentStep().process(context)

    record = database_session.add.call_args.args[0]
    assert record.humanizer_model_name is None
    assert record.humanizer_prompt_version is None
