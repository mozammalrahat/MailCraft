"""Build prompts for the content humanization pass."""

from app.prompts.templates.content_humanizer import CONTENT_HUMANIZER_SYSTEM_RULES

HUMANIZER_PROMPT_VERSION = "1.0.0"


def build_content_humanizer_prompt(
    *,
    subject: str | None,
    body: str,
    content_type_label: str,
    tone_label: str,
    must_preserve_facts: list[str] | None = None,
) -> str:
    """Build a humanization prompt for a generated subject and body."""
    subject_line = subject.strip() if subject else "(none)"
    facts_block = ""
    if must_preserve_facts:
        facts = "\n".join(f"- {fact}" for fact in must_preserve_facts if fact.strip())
        if facts:
            facts_block = f"\nFACTS THAT MUST REMAIN IN THE REWRITE:\n{facts}\n"

    return f"""{CONTENT_HUMANIZER_SYSTEM_RULES}

DOCUMENT TYPE: {content_type_label}
TONE: {tone_label}
{facts_block}
SOURCE SUBJECT:
{subject_line}

SOURCE BODY:
{body.strip()}

Rewrite the source so it sounds human-written while following every rule above.
Return only the rewritten content in the required output format.
""".strip()
