from app.api.dependencies.authentication import CurrentUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.application.services.scenario_service import ScenarioService
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.schemas.scenario import (
    ScenarioCreateRequest,
    ScenarioResponse,
    ScenarioUpdateRequest,
)
from fastapi import APIRouter, Query

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios(
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    purpose: ApplicationPurpose | None = None,
    document_type: DocumentType | None = None,
) -> list[ScenarioResponse]:
    service = ScenarioService(database_session)
    scenarios = service.list_for_user(
        current_user.id,
        purpose=purpose,
        document_type=document_type,
    )
    return [ScenarioResponse.model_validate(scenario) for scenario in scenarios]


@router.post("", response_model=ScenarioResponse, status_code=201)
def create_scenario(
    payload: ScenarioCreateRequest,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> ScenarioResponse:
    service = ScenarioService(database_session)
    return ScenarioResponse.model_validate(service.create(current_user.id, payload))


@router.patch("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdateRequest,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> ScenarioResponse:
    service = ScenarioService(database_session)
    return ScenarioResponse.model_validate(
        service.update_owned(current_user.id, scenario_id, payload)
    )


@router.post("/{scenario_id}/clone", response_model=ScenarioResponse, status_code=201)
def clone_scenario(
    scenario_id: int,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
    name: str | None = Query(default=None),
) -> ScenarioResponse:
    service = ScenarioService(database_session)
    return ScenarioResponse.model_validate(
        service.clone_owned(current_user.id, scenario_id, name=name)
    )


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: int,
    database_session: DatabaseSessionDependency,
    current_user: CurrentUserDependency,
) -> None:
    service = ScenarioService(database_session)
    service.delete_owned(current_user.id, scenario_id)
