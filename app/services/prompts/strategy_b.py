from app.services.prompts._helpers import format_key_facts_bulleted
from app.services.prompts._render import render_prompt
from app.services.prompts._tone import get_tone_guidance
from app.services.prompts.templates.parts.structure import OUTPUT_FORMAT
from app.services.prompts.templates.strategy_b import STRATEGY_B_TEMPLATE


def build_strategy_b_prompt(intent: str, key_facts: list[str], tone: str) -> str:
    return render_prompt(
        STRATEGY_B_TEMPLATE,
        intent=intent,
        key_facts=format_key_facts_bulleted(key_facts),
        tone=tone,
        tone_guidance=get_tone_guidance(tone),
        output_format=OUTPUT_FORMAT,
    )
