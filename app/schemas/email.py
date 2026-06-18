from pydantic import BaseModel, Field


class EmailGenerationRequest(BaseModel):
    intent: str = Field(..., min_length=1, description="Core purpose of the email")
    key_facts: list[str] = Field(
        default_factory=list,
        description="Facts that must appear in the generated email",
    )
    tone: str = Field(..., min_length=1, description="Desired email tone")


class EmailGenerationResponse(BaseModel):
    email: str
    model: str
