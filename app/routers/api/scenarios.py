from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Scenario, User
from app.db.session import get_db
from app.schemas.stateful import (
    DocumentType,
    Purpose,
    ScenarioCreate,
    ScenarioOut,
    ScenarioUpdate,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

DbDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(
    db: DbDep,
    user: CurrentUserDep,
    purpose: Purpose | None = None,
    document_type: DocumentType | None = None,
) -> list[Scenario]:
    query = db.query(Scenario).filter(Scenario.user_id == user.id)
    if purpose:
        query = query.filter(Scenario.purpose == purpose.value)
    if document_type:
        query = query.filter(Scenario.document_type == document_type.value)
    return query.order_by(Scenario.updated_at.desc()).all()


@router.post("", response_model=ScenarioOut, status_code=201)
def create_scenario(
    payload: ScenarioCreate,
    db: DbDep,
    user: CurrentUserDep,
) -> Scenario:
    scenario = Scenario(
        user_id=user.id,
        name=payload.name,
        purpose=payload.purpose.value,
        document_type=payload.document_type.value,
        system_prompt=payload.system_prompt,
        is_default=False,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.patch("/{scenario_id}", response_model=ScenarioOut)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    db: DbDep,
    user: CurrentUserDep,
) -> Scenario:
    scenario = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.user_id == user.id)
        .first()
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if payload.name is not None:
        scenario.name = payload.name
    if payload.system_prompt is not None:
        scenario.system_prompt = payload.system_prompt

    db.commit()
    db.refresh(scenario)
    return scenario


@router.post("/{scenario_id}/clone", response_model=ScenarioOut, status_code=201)
def clone_scenario(
    scenario_id: int,
    db: DbDep,
    user: CurrentUserDep,
    name: str | None = Query(default=None),
) -> Scenario:
    source = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.user_id == user.id)
        .first()
    )
    if source is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    clone = Scenario(
        user_id=user.id,
        name=name or f"{source.name} (copy)",
        purpose=source.purpose,
        document_type=source.document_type,
        system_prompt=source.system_prompt,
        is_default=False,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: int,
    db: DbDep,
    user: CurrentUserDep,
) -> None:
    scenario = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.user_id == user.id)
        .first()
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    remaining = (
        db.query(Scenario)
        .filter(
            Scenario.user_id == user.id,
            Scenario.purpose == scenario.purpose,
            Scenario.document_type == scenario.document_type,
            Scenario.id != scenario.id,
        )
        .count()
    )
    if remaining == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the last scenario for this purpose and document type",
        )

    db.delete(scenario)
    db.commit()
