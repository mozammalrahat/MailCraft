"""GenerationJobService unit tests."""

import pytest
from app.application.services.authentication_service import register_user
from app.application.services.generation_job_service import GenerationJobService
from app.database.engine_manager import get_database_engine_manager
from app.domain.enums.generation_kind import GenerationKind
from fastapi import HTTPException


@pytest.fixture
def database_session():
    factory = get_database_engine_manager().get_session_factory()
    session = factory()
    yield session
    session.close()


def test_generation_job_service_create_and_get_owned(database_session) -> None:
    user = register_user(database_session, "jobs@example.com", "password123")
    service = GenerationJobService(database_session)
    job = service.create_job(
        user_id=user.id,
        kind=GenerationKind.LEGACY_EMAIL.value,
        payload={"intent": "Follow up", "key_facts": ["Fact"], "tone": "formal"},
    )

    loaded = service.get_owned(user.id, job.id)
    assert loaded.status == "queued"


def test_generation_job_service_rejects_foreign_owner(database_session) -> None:
    user = register_user(database_session, "owner-jobs@example.com", "password123")
    service = GenerationJobService(database_session)
    job = service.create_job(
        user_id=user.id,
        kind=GenerationKind.LEGACY_EMAIL.value,
        payload={"intent": "Follow up", "key_facts": ["Fact"], "tone": "formal"},
    )

    with pytest.raises(HTTPException) as exc:
        service.get_owned(user_id=user.id + 999, job_id=job.id)

    assert exc.value.status_code == 404
