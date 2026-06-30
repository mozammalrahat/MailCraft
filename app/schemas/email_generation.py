"""Legacy email generation schemas."""

from pydantic import BaseModel, Field, field_validator

from app.domain.enums.email_strategy import EmailStrategy
from app.domain.enums.email_tone import EmailTone


class EmailGenerationRequest(BaseModel):
    """Request body for legacy email generation."""

    intent: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Core purpose of the email",
    )
    key_facts: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
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
        """Ensure at least one non-empty key fact, enforce per-fact length."""
        cleaned = [fact.strip() for fact in facts if fact.strip()]
        if not cleaned:
            message = "At least one non-empty key fact is required"
            raise ValueError(message)
        for fact in cleaned:
            if len(fact) > 500:
                raise ValueError("Each key fact must be 500 characters or fewer")
        return cleaned


class EmailGenerationResponse(BaseModel):
    """Response for legacy email generation."""

    email: str
    subject: str | None = None
    model: str
    strategy: str
    prompt_version: str
    generated_content_id: int | None = None
    raw_email: str | None = None
    raw_subject: str | None = None
