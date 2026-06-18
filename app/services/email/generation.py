import logging
import re

from app.config import Settings
from app.schemas.email import EmailGenerationRequest, EmailGenerationResponse
from app.services.email.prompt_builder import build_prompt, get_prompt_version
from app.services.errors import ServiceValidationError
from app.services.llm.client import LlmClient

logger = logging.getLogger(__name__)

_SUBJECT_PATTERN = re.compile(r"^Subject:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def _parse_email_output(raw: str) -> tuple[str | None, str]:
    match = _SUBJECT_PATTERN.search(raw)
    if not match:
        return None, raw.strip()

    subject = match.group(1).strip()
    body = raw[match.end() :].strip()
    return subject, body


def _format_email(subject: str | None, body: str) -> str:
    return body


async def generate_email(
    request: EmailGenerationRequest,
    llm_client: LlmClient,
    settings: Settings,
) -> EmailGenerationResponse:
    if not request.key_facts:
        raise ServiceValidationError("At least one key fact is required")

    strategy_key = request.strategy.value
    strategy_config = settings.strategies.get(strategy_key)
    if strategy_config is None:
        raise ServiceValidationError(f"Unknown strategy: {strategy_key}")

    prompt = build_prompt(request, strategy=strategy_key)

    logger.info(
        "generating email",
        extra={
            "strategy": strategy_key,
            "model": strategy_config.model,
            "tone": request.tone.value,
            "fact_count": len(request.key_facts),
        },
    )

    raw_output = await llm_client.generate_content(
        prompt,
        model=strategy_config.model,
    )
    subject, body = _parse_email_output(raw_output)
    formatted_email = _format_email(subject, body)

    return EmailGenerationResponse(
        email=formatted_email,
        subject=subject,
        model=strategy_config.model,
        strategy=strategy_key,
        prompt_version=get_prompt_version(),
    )
