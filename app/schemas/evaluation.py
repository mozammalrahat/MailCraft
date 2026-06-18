from pydantic import BaseModel, Field

from app.schemas.email import EmailTone


class Scenario(BaseModel):
    id: str = Field(..., min_length=1, description="Unique scenario identifier")
    intent: str = Field(..., min_length=1)
    key_facts: list[str] = Field(..., min_length=1)
    tone: EmailTone
    reference_email: str = Field(..., min_length=1)


class ScenarioCollection(BaseModel):
    scenarios: list[Scenario] = Field(..., min_length=1)

    @property
    def count(self) -> int:
        return len(self.scenarios)
