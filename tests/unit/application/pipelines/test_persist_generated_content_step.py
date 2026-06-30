from unittest.mock import MagicMock

import pytest
from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.steps.persist_generated_content_step import (
    PersistGeneratedContentStep,
)
from app.core.configuration import Settings
from app.domain.enums.generation_kind import GenerationKind


@pytest.mark.asyncio
async def test_persist_generated_content_stores_humanizer_metadata() -> None:
    database_session = MagicMock()
    context = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=Settings(
            google_api_key="test-key",
            GOOGLE_MODEL_A="gemini-test",
        ),
        database_session=database_session,
        language_model_client=MagicMock(),
    )
    context.subject = "Humanized subject"
    context.body = "Humanized body"
    context.raw_subject = "Raw subject"
    context.raw_body = "Raw body"
    context.humanization_applied = True
    context.humanizer_model_name = "gemini-humanizer"
    context.humanizer_prompt_version = "1.1.0"
    context.intent = "Follow up"
    context.key_facts = ["Fact one"]
    context.model_name = "gemini-test"
    context.prompt_version = "2.0.0"

    await PersistGeneratedContentStep().process(context)

    record = database_session.add.call_args.args[0]
    assert record.humanizer_model_name == "gemini-humanizer"
    assert record.humanizer_prompt_version == "1.1.0"


@pytest.mark.asyncio
async def test_persist_generated_content_omits_humanizer_metadata_on_fallback() -> None:
    database_session = MagicMock()
    context = GenerationContext(
        user_id=1,
        generation_kind=GenerationKind.LEGACY_EMAIL,
        settings=Settings(
            google_api_key="test-key",
            GOOGLE_MODEL_A="gemini-test",
        ),
        database_session=database_session,
        language_model_client=MagicMock(),
    )
    context.subject = "Raw subject"
    context.body = "Raw body"
    context.humanization_applied = False
    context.humanizer_model_name = None
    context.humanizer_prompt_version = None
    context.intent = "Follow up"
    context.key_facts = ["Fact one"]
    context.model_name = "gemini-test"
    context.prompt_version = "2.0.0"

    await PersistGeneratedContentStep().process(context)

    record = database_session.add.call_args.args[0]
    assert record.humanizer_model_name is None
    assert record.humanizer_prompt_version is None
