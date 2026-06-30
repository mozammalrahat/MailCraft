from typing import Annotated

from app.api.dependencies.authentication import AuthenticatedPageUserDependency
from app.api.dependencies.database import DatabaseSessionDependency
from app.application.services.generated_content_service import (
    GeneratedContentFilters,
    GeneratedContentService,
)
from app.application.services.scenario_service import ScenarioService
from app.core.configuration import Settings, get_settings
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

SettingsDep = Annotated[Settings, Depends(get_settings)]


def _optional_query_str(value: str | None) -> str | None:
    """Treat blank HTML form values as unset query parameters."""
    if value is None or not value.strip():
        return None
    return value.strip()


def _optional_query_int(value: str | None) -> int | None:
    """Parse optional integer query params from HTML forms."""
    cleaned = _optional_query_str(value)
    if cleaned is None:
        return None
    return int(cleaned)


@router.get("")
def dashboard_home(
    request: Request,
    database_session: DatabaseSessionDependency,
    settings: SettingsDep,
    page_user: AuthenticatedPageUserDependency,
    generation_kind: str | None = None,
    purpose: str | None = None,
    document_type: str | None = None,
    scenario_id: str | None = None,
    q: str | None = None,
):
    if isinstance(page_user, RedirectResponse):
        return page_user

    parsed_generation_kind = _optional_query_str(generation_kind)
    parsed_purpose = _optional_query_str(purpose)
    parsed_document_type = _optional_query_str(document_type)
    parsed_scenario_id = _optional_query_int(scenario_id)
    parsed_query = _optional_query_str(q)

    content_service = GeneratedContentService(database_session)
    scenario_service = ScenarioService(database_session)
    documents, _ = content_service.list_for_user(
        page_user.id,
        filters=GeneratedContentFilters(
            generation_kind=parsed_generation_kind,
            purpose=parsed_purpose,
            document_type=parsed_document_type,
            scenario_id=parsed_scenario_id,
            query_text=parsed_query,
        ),
        limit=50,
    )
    scenarios = scenario_service.list_for_user(page_user.id)
    stats = content_service.get_dashboard_stats(page_user.id)

    return templates.TemplateResponse(
        request,
        "pages/dashboard/index.html",
        {
            "user": page_user,
            "documents": documents,
            "scenarios": scenarios,
            "stats": stats,
            "purposes": [p.value for p in ApplicationPurpose],
            "document_types": [d.value for d in DocumentType],
            "generation_kinds": [k.value for k in GenerationKind],
            "filters": {
                "generation_kind": parsed_generation_kind or "",
                "purpose": parsed_purpose or "",
                "document_type": parsed_document_type or "",
                "scenario_id": (
                    parsed_scenario_id if parsed_scenario_id is not None else ""
                ),
                "q": parsed_query or "",
            },
            "debug": settings.debug,
        },
    )


@router.get("/generate")
def dashboard_generate(
    request: Request,
    database_session: DatabaseSessionDependency,
    settings: SettingsDep,
    page_user: AuthenticatedPageUserDependency,
):
    if isinstance(page_user, RedirectResponse):
        return page_user

    scenarios = ScenarioService(database_session).list_for_user(page_user.id)
    scenarios = sorted(scenarios, key=lambda scenario: scenario.name)
    scenario_json = [
        {
            "id": scenario.id,
            "name": scenario.name,
            "purpose": scenario.purpose,
            "document_type": scenario.document_type,
        }
        for scenario in scenarios
    ]

    return templates.TemplateResponse(
        request,
        "pages/dashboard/generate.html",
        {
            "user": page_user,
            "scenarios": scenarios,
            "scenarios_json": scenario_json,
            "purposes": [p.value for p in ApplicationPurpose],
            "document_types": [d.value for d in DocumentType],
        },
    )


@router.get("/scenarios")
def dashboard_scenarios(
    request: Request,
    database_session: DatabaseSessionDependency,
    settings: SettingsDep,
    page_user: AuthenticatedPageUserDependency,
):
    if isinstance(page_user, RedirectResponse):
        return page_user

    scenarios = ScenarioService(database_session).list_for_user(page_user.id)
    scenarios = sorted(
        scenarios,
        key=lambda scenario: (
            scenario.purpose,
            scenario.document_type,
            scenario.name,
        ),
    )

    return templates.TemplateResponse(
        request,
        "pages/dashboard/scenarios.html",
        {"user": page_user, "scenarios": scenarios},
    )


@router.get("/scenarios/{scenario_id}/edit")
def dashboard_scenario_editor(
    scenario_id: int,
    request: Request,
    database_session: DatabaseSessionDependency,
    settings: SettingsDep,
    page_user: AuthenticatedPageUserDependency,
):
    if isinstance(page_user, RedirectResponse):
        return page_user

    try:
        scenario = ScenarioService(database_session).get_owned(
            page_user.id,
            scenario_id,
        )
    except HTTPException:
        return RedirectResponse("/dashboard/scenarios", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/dashboard/scenario_editor.html",
        {"user": page_user, "scenario": scenario},
    )
