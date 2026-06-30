"""GeneratedContentService unit tests."""

import pytest
from app.application.services.authentication_service import register_user
from app.application.services.generated_content_service import (
    GeneratedContentFilters,
    GeneratedContentService,
)
from app.database.engine_manager import get_database_engine_manager
from app.domain.enums.generation_kind import GenerationKind
from fastapi import HTTPException


@pytest.fixture
def database_session():
    factory = get_database_engine_manager().get_session_factory()
    session = factory()
    yield session
    session.close()


def test_list_for_user_filters_by_generation_kind(database_session) -> None:
    user = register_user(database_session, "content@example.com", "password123")
    service = GeneratedContentService(database_session)

    records, total = service.list_for_user(
        user.id,
        filters=GeneratedContentFilters(
            generation_kind=GenerationKind.LEGACY_EMAIL.value
        ),
    )

    assert total == 0
    assert records == []


def test_get_owned_raises_for_missing_record(database_session) -> None:
    user = register_user(database_session, "missing@example.com", "password123")
    service = GeneratedContentService(database_session)

    with pytest.raises(HTTPException) as exc_info:
        service.get_owned(user.id, 9999)

    assert exc_info.value.status_code == 404


def test_get_dashboard_stats_returns_zero_counts(database_session) -> None:
    user = register_user(database_session, "stats@example.com", "password123")
    service = GeneratedContentService(database_session)

    stats = service.get_dashboard_stats(user.id)

    assert stats["total"] == 0
    assert stats["legacy_emails"] == 0
    assert stats["scenarios"] == 6
