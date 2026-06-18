from app.schemas.email import EmailGenerationRequest
from app.services.prompts import PROMPT_BUILDERS

PROMPT_VERSION = "2.0.0"

SUPPORTED_STRATEGIES = frozenset(PROMPT_BUILDERS.keys())


def build_prompt(request: EmailGenerationRequest, strategy: str = "strategy_a") -> str:
    builder = PROMPT_BUILDERS.get(strategy)
    if builder is None:
        msg = f"Unsupported strategy: {strategy}"
        raise ValueError(msg)

    return builder(
        request.intent,
        request.key_facts,
        request.tone.value,
    )


def get_prompt_version() -> str:
    return PROMPT_VERSION
