from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class EmailTone(StrEnum):
    FORMAL = "formal"
    CASUAL = "casual"
    URGENT = "urgent"
    EMPATHETIC = "empathetic"


class EmailStrategy(StrEnum):
    STRATEGY_A = "strategy_a"
    STRATEGY_B = "strategy_b"


class EmailGenerationRequest(BaseModel):
    intent: str = Field(..., min_length=1, description="Core purpose of the email")
    key_facts: list[str] = Field(
        ...,
        min_length=1,
        description="Facts that must appear in the generated email",
    )
    tone: EmailTone = Field(..., description="Desired email tone")
    strategy: EmailStrategy = Field(
        default=EmailStrategy.STRATEGY_A,
        description="Prompting strategy to use",
    )

    @field_validator("key_facts")
    @classmethod
    def validate_key_facts(cls, facts: list[str]) -> list[str]:
        cleaned = [fact.strip() for fact in facts if fact.strip()]
        if not cleaned:
            msg = "At least one non-empty key fact is required"
            raise ValueError(msg)
        return cleaned


class EmailGenerationResponse(BaseModel):
    email: str
    subject: str | None = None
    model: str
    strategy: str
    prompt_version: str
