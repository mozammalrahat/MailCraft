from datetime import datetime

from pydantic import BaseModel, Field
from tools.evaluation.metrics.base import MetricDefinition

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


class ScenarioScore(BaseModel):
    scenario_id: str
    scores: dict[str, float]
    generated_email: str


class StrategyResult(BaseModel):
    model: str
    scenarios: list[ScenarioScore]
    averages: dict[str, float]


class EvaluationMetadata(BaseModel):
    generated_at: datetime
    metrics: list[MetricDefinition]


class EvaluationSummary(BaseModel):
    overall_average: float


class EvaluationReport(BaseModel):
    metadata: EvaluationMetadata
    strategies: dict[str, StrategyResult]
    summary: EvaluationSummary
