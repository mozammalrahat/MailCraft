from app.services.prompts._render import render_prompt
from app.services.prompts.templates.judge_tone import JUDGE_TONE_TEMPLATE
from app.services.prompts.templates.parts.judge import TONE_JUDGE_RUBRIC


def build_tone_judge_prompt(tone: str, generated_email: str) -> str:
    return render_prompt(
        JUDGE_TONE_TEMPLATE,
        tone=tone,
        tone_rubric=TONE_JUDGE_RUBRIC,
        generated_email=generated_email,
    )
