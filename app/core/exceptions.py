"""Application-wide exception types."""


class LlmError(Exception):
    """Raised when the LLM provider returns an error or unreachable."""

    def __init__(self, message: str = "LLM request failed") -> None:
        self.message = message
        super().__init__(message)


class ServiceValidationError(Exception):
    """Raised when business validation fails beyond Pydantic schema checks."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
