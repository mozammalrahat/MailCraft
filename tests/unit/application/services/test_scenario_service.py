"""ScenarioService unit tests."""

import pytest
from app.application.services.authentication_service import register_user
from app.application.services.scenario_service import ScenarioService
from app.database.engine_manager import get_database_engine_manager
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.schemas.scenario import ScenarioCreateRequest, ScenarioUpdateRequest
from fastapi import HTTPException


@pytest.fixture
def database_session():
    factory = get_database_engine_manager().get_session_factory()
    session = factory()
    yield session
    session.close()


def test_list_for_user_returns_seeded_defaults(database_session) -> None:
    user = register_user(database_session, "scenario@example.com", "password123")
    service = ScenarioService(database_session)

    scenarios = service.list_for_user(user.id)

    assert len(scenarios) == 6


def test_create_and_update_owned(database_session) -> None:
    user = register_user(database_session, "create@example.com", "password123")
    service = ScenarioService(database_session)
    created = service.create(
        user.id,
        ScenarioCreateRequest(
            name="Custom Interview Email",
            purpose=ApplicationPurpose.INTERVIEW,
            document_type=DocumentType.EMAIL,
            system_prompt="Write a concise interview email.",
        ),
    )

    updated = service.update_owned(
        user.id,
        created.id,
        ScenarioUpdateRequest(name="Updated Interview Email"),
    )

    assert updated.name == "Updated Interview Email"


def test_get_owned_raises_for_other_user(database_session) -> None:
    owner = register_user(database_session, "owner@example.com", "password123")
    other = register_user(database_session, "other@example.com", "password123")
    service = ScenarioService(database_session)
    scenarios = service.list_for_user(owner.id)

    with pytest.raises(HTTPException) as exc_info:
        service.get_owned(other.id, scenarios[0].id)

    assert exc_info.value.status_code == 404
