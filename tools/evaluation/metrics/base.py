from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class MetricInput(BaseModel):
    """Input for evaluation metrics."""

    generated_email: str  # Full clipboard text (subject + body), not body alone.
    key_facts: list[str] = Field(default_factory=list)
    tone: str = ""
    reference_email: str | None = None


class MetricScore(BaseModel):
    name: str
    value: float = Field(ge=0.0, le=1.0)
    details: str = ""


class MetricDefinition(BaseModel):
    name: str
    definition: str
    logic: str
    technique: str


@runtime_checkable
class Metric(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def definition(self) -> MetricDefinition: ...

    async def score(self, input_data: MetricInput) -> MetricScore: ...
