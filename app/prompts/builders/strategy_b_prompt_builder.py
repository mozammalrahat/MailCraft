"""Build Strategy B legacy email prompts."""

from app.prompts.builders.key_facts_formatter import format_key_facts_bulleted
from app.prompts.builders.prompt_renderer import render_prompt
from app.prompts.builders.tone_guidance import get_tone_guidance
from app.prompts.templates.parts.structure import OUTPUT_FORMAT
from app.prompts.templates.strategy_b import STRATEGY_B_TEMPLATE


def build_strategy_b_prompt(intent: str, key_facts: list[str], tone: str) -> str:
    """Assemble the Strategy B prompt from static templates and inputs."""
    return render_prompt(
        STRATEGY_B_TEMPLATE,
        intent=intent,
        key_facts=format_key_facts_bulleted(key_facts),
        tone=tone,
        tone_guidance=get_tone_guidance(tone),
        output_format=OUTPUT_FORMAT,
    )
