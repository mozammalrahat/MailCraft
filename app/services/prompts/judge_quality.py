from app.services.prompts._render import render_prompt
from app.services.prompts.templates.judge_quality import JUDGE_QUALITY_TEMPLATE
from app.services.prompts.templates.parts.judge import QUALITY_JUDGE_RUBRIC


def build_quality_judge_prompt(generated_email: str) -> str:
    return render_prompt(
        JUDGE_QUALITY_TEMPLATE,
        quality_rubric=QUALITY_JUDGE_RUBRIC,
        generated_email=generated_email,
    )
