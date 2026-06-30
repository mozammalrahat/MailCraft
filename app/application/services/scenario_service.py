"""Scenario CRUD service."""

from app.database.models.scenario import Scenario
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType
from app.schemas.scenario import ScenarioCreateRequest, ScenarioUpdateRequest
from fastapi import HTTPException
from sqlalchemy.orm import Session


class ScenarioService:
    """Owns scenario queries and mutations."""

    def __init__(self, database_session: Session) -> None:
        self._database_session = database_session

    def list_for_user(
        self,
        user_id: int,
        *,
        purpose: ApplicationPurpose | None = None,
        document_type: DocumentType | None = None,
    ) -> list[Scenario]:
        """List scenarios owned by a user."""
        query = self._database_session.query(Scenario).filter(
            Scenario.user_id == user_id
        )
        if purpose:
            query = query.filter(Scenario.purpose == purpose.value)
        if document_type:
            query = query.filter(Scenario.document_type == document_type.value)
        return query.order_by(Scenario.updated_at.desc()).all()

    def get_owned(self, user_id: int, scenario_id: int) -> Scenario:
        """Load a scenario owned by the user."""
        scenario = (
            self._database_session.query(Scenario)
            .filter(Scenario.id == scenario_id, Scenario.user_id == user_id)
            .first()
        )
        if scenario is None:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario

    def create(self, user_id: int, payload: ScenarioCreateRequest) -> Scenario:
        """Create a scenario for a user."""
        scenario = Scenario(
            user_id=user_id,
            name=payload.name,
            purpose=payload.purpose.value,
            document_type=payload.document_type.value,
            system_prompt=payload.system_prompt,
            is_default=False,
        )
        self._database_session.add(scenario)
        self._database_session.commit()
        self._database_session.refresh(scenario)
        return scenario

    def update_owned(
        self,
        user_id: int,
        scenario_id: int,
        payload: ScenarioUpdateRequest,
    ) -> Scenario:
        """Update a scenario owned by the user."""
        scenario = self.get_owned(user_id, scenario_id)
        if payload.name is not None:
            scenario.name = payload.name
        if payload.system_prompt is not None:
            scenario.system_prompt = payload.system_prompt
        self._database_session.commit()
        self._database_session.refresh(scenario)
        return scenario

    def clone_owned(
        self,
        user_id: int,
        scenario_id: int,
        *,
        name: str | None = None,
    ) -> Scenario:
        """Clone a scenario owned by the user."""
        source = self.get_owned(user_id, scenario_id)
        clone = Scenario(
            user_id=user_id,
            name=name or f"{source.name} (copy)",
            purpose=source.purpose,
            document_type=source.document_type,
            system_prompt=source.system_prompt,
            is_default=False,
        )
        self._database_session.add(clone)
        self._database_session.commit()
        self._database_session.refresh(clone)
        return clone

    def delete_owned(self, user_id: int, scenario_id: int) -> None:
        """Delete a scenario owned by the user."""
        scenario = self.get_owned(user_id, scenario_id)
        remaining = (
            self._database_session.query(Scenario)
            .filter(
                Scenario.user_id == user_id,
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
        self._database_session.delete(scenario)
        self._database_session.commit()
