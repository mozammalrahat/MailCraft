from unittest.mock import MagicMock

import pytest
from app.application.pipelines.generation_context import GenerationContext
from app.application.pipelines.steps.store_resume_files_step import StoreResumeFilesStep
from app.domain.enums.generation_kind import GenerationKind
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from tests.support.settings_factory import build_test_settings


@pytest.mark.asyncio
async def test_store_resume_files_step_persists_when_enabled(tmp_path) -> None:
    settings = build_test_settings(
        upload_dir=str(tmp_path / "uploads"),
        store_uploaded_resumes=True,
    )
    storage = LocalFileStorage(settings)
    context = GenerationContext(
        user_id=3,
        generation_kind=GenerationKind.APPLICATION_DOCUMENT,
        settings=settings,
        database_session=MagicMock(),
        language_model_client=MagicMock(),
        resume_file_payloads=[("cv.pdf", b"%PDF-1.4 cv")],
        file_storage=storage,
    )

    result = await StoreResumeFilesStep().process(context)

    assert len(result.resume_storage_keys) == 1
    assert storage.exists(result.resume_storage_keys[0]["key"])
