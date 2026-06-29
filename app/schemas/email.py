"""Backward-compatible email schema re-exports."""

from app.domain.enums.email_strategy import EmailStrategy
from app.domain.enums.email_tone import EmailTone
from app.schemas.email_generation import EmailGenerationRequest, EmailGenerationResponse

__all__ = [
    "EmailGenerationRequest",
    "EmailGenerationResponse",
    "EmailStrategy",
    "EmailTone",
]
