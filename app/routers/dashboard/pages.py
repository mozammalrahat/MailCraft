from typing import Annotated

from app.config import Settings, get_settings
from app.database.models.generated_content import GeneratedContent
from app.database.models.scenario import Scenario
from app.database.models.user import User
from app.db.models import get_db
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.domain.enums.generation_kind import GenerationKind
from app.services.auth_service import ACCESS_COOKIE, get_user_from_access_token
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

DatabaseSessionDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _get_user_or_redirect(
    request: Request, database_session: Session, settings: Settings,
) -> User | RedirectResponse:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        return RedirectResponse("/auth/login", status_code=303)
    try:
        return get_user_from_access_token(database_session, token, settings)
    except Exception:
        return RedirectResponse("/auth/login", status_code=303)


@router.get("")
def dashboard_home(
    request: Request,
    database_session: DatabaseSessionDep,
    settings: SettingsDep,
    generation_kind: str | None = None,
    purpose: str | None = None,
    document_type: str | None = None,
    scenario_id: int | None = None,
    q: str | None = None,
):
    user = _get_user_or_redirect(request, database_session, settings)
    if isinstance(user, RedirectResponse):
        return user

    query = database_session.query(GeneratedContent).filter(
        GeneratedContent.user_id == user.id
    )
    if generation_kind:
        query = query.filter(GeneratedContent.generation_kind == generation_kind)
    if purpose:
        query = query.filter(GeneratedContent.purpose == purpose)
    if document_type:
        query = query.filter(GeneratedContent.document_type == document_type)
    if scenario_id:
        query = query.filter(GeneratedContent.scenario_id == scenario_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            GeneratedContent.position_description.ilike(like)
            | GeneratedContent.metadata_json.ilike(like)
            | GeneratedContent.subject.ilike(like)
            | GeneratedContent.intent.ilike(like)
        )

    documents = query.order_by(GeneratedContent.created_at.desc()).limit(50).all()
    scenarios = (
        database_session.query(Scenario).filter(Scenario.user_id == user.id).all()
    )
    base_query = database_session.query(GeneratedContent).filter(
        GeneratedContent.user_id == user.id
    )

    stats = {
        "total": base_query.count(),
        "legacy_emails": base_query.filter(
            GeneratedContent.generation_kind == GenerationKind.LEGACY_EMAIL.value
        ).count(),
        "application_documents": base_query.filter(
            GeneratedContent.generation_kind
            == GenerationKind.APPLICATION_DOCUMENT.value
        ).count(),
        "interview": base_query.filter(
            GeneratedContent.purpose == ApplicationPurpose.INTERVIEW.value
        ).count(),
        "ms": base_query.filter(
            GeneratedContent.purpose == ApplicationPurpose.MS.value
        ).count(),
        "phd": base_query.filter(
            GeneratedContent.purpose == ApplicationPurpose.PHD.value
        ).count(),
        "emails": base_query.filter(
            GeneratedContent.document_type == DocumentType.EMAIL.value
        ).count(),
        "cover_letters": base_query.filter(
            GeneratedContent.document_type == DocumentType.COVER_LETTER.value
        ).count(),
        "scenarios": len(scenarios),
    }

    return templates.TemplateResponse(
        request,
        "pages/dashboard/index.html",
        {
            "user": user,
            "documents": documents,
            "scenarios": scenarios,
            "stats": stats,
            "purposes": [p.value for p in ApplicationPurpose],
            "document_types": [d.value for d in DocumentType],
            "generation_kinds": [k.value for k in GenerationKind],
            "filters": {
                "generation_kind": generation_kind or "",
                "purpose": purpose or "",
                "document_type": document_type or "",
                "scenario_id": scenario_id or "",
                "q": q or "",
            },
            "debug": settings.debug,
        },
    )


@router.get("/generate")
def dashboard_generate(
    request: Request, database_session: DatabaseSessionDep, settings: SettingsDep,
):
    user = _get_user_or_redirect(request, database_session, settings)
    if isinstance(user, RedirectResponse):
        return user

    scenarios = (
        database_session.query(Scenario)
        .filter(Scenario.user_id == user.id)
        .order_by(Scenario.name)
        .all()
    )
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
            "user": user,
            "scenarios": scenarios,
            "scenarios_json": scenario_json,
            "purposes": [p.value for p in ApplicationPurpose],
            "document_types": [d.value for d in DocumentType],
        },
    )


@router.get("/scenarios")
def dashboard_scenarios(
    request: Request, database_session: DatabaseSessionDep, settings: SettingsDep,
):
    user = _get_user_or_redirect(request, database_session, settings)
    if isinstance(user, RedirectResponse):
        return user

    scenarios = (
        database_session.query(Scenario)
        .filter(Scenario.user_id == user.id)
        .order_by(Scenario.purpose, Scenario.document_type, Scenario.name)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "pages/dashboard/scenarios.html",
        {"user": user, "scenarios": scenarios},
    )


@router.get("/scenarios/{scenario_id}/edit")
def dashboard_scenario_editor(
    scenario_id: int,
    request: Request,
    database_session: DatabaseSessionDep,
    settings: SettingsDep,
):
    user = _get_user_or_redirect(request, database_session, settings)
    if isinstance(user, RedirectResponse):
        return user

    scenario = (
        database_session.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.user_id == user.id)
        .first()
    )
    if scenario is None:
        return RedirectResponse("/dashboard/scenarios", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/dashboard/scenario_editor.html",
        {"user": user, "scenario": scenario},
    )
