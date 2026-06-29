"""Legacy email generation helpers."""

import re

from app.prompts.builders import PROMPT_BUILDERS

PROMPT_VERSION = "2.0.0"

_SUBJECT_PATTERN = re.compile(r"^Subject:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def build_legacy_email_prompt(
    intent: str,
    key_facts: list[str],
    tone: str,
    strategy: str,
) -> str:
    """Build a legacy email prompt for the given strategy."""
    builder = PROMPT_BUILDERS.get(strategy)
    if builder is None:
        message = f"Unsupported strategy: {strategy}"
        raise ValueError(message)
    return builder(intent, key_facts, tone)


def parse_legacy_email_output(raw_output: str) -> tuple[str | None, str]:
    """Parse subject and body from raw legacy email output."""
    match = _SUBJECT_PATTERN.search(raw_output)
    if not match:
        return None, raw_output.strip()

    subject = match.group(1).strip()
    body = raw_output[match.end() :].strip()
    return subject, body
