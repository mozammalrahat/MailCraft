from app.prompts.builders.judge_quality_prompt_builder import build_quality_judge_prompt
from app.prompts.builders.judge_tone_prompt_builder import build_tone_judge_prompt
from app.prompts.builders.strategy_a_prompt_builder import build_strategy_a_prompt
from app.prompts.builders.strategy_b_prompt_builder import build_strategy_b_prompt
from app.prompts.builders.tone_guidance import get_tone_guidance
from app.prompts.templates.strategy_a import STRATEGY_A_TEMPLATE
from app.prompts.templates.strategy_b import STRATEGY_B_TEMPLATE


def test_strategy_b_template_uses_placeholders_only() -> None:
    assert "{intent}" in STRATEGY_B_TEMPLATE
    assert "{key_facts}" in STRATEGY_B_TEMPLATE
    assert "{tone}" in STRATEGY_B_TEMPLATE
    assert "{tone_guidance}" in STRATEGY_B_TEMPLATE
    assert "{output_format}" in STRATEGY_B_TEMPLATE
    assert "Schedule kickoff" not in STRATEGY_B_TEMPLATE


def test_strategy_a_template_uses_placeholders_only() -> None:
    assert "{intent}" in STRATEGY_A_TEMPLATE
    assert "{key_facts}" in STRATEGY_A_TEMPLATE
    assert "{role}" in STRATEGY_A_TEMPLATE
    assert "{few_shot_examples}" in STRATEGY_A_TEMPLATE
    assert "Schedule kickoff" not in STRATEGY_A_TEMPLATE


def test_strategy_a_prompt_includes_inputs() -> None:
    prompt = build_strategy_a_prompt(
        intent="Schedule kickoff",
        key_facts=["June 5 at 10 AM", "Product and engineering leads"],
        tone="formal",
    )

    assert "Schedule kickoff" in prompt
    assert "June 5 at 10 AM" in prompt
    assert "formal" in prompt
    assert "Example 1" in prompt
    assert "Example 4" in prompt
    assert "professional email composer" in prompt
    assert "Writing framework" in prompt
    assert "Avoid:" in prompt


def test_strategy_a_includes_tone_guidance() -> None:
    prompt = build_strategy_a_prompt(
        intent="Apologize for delay",
        key_facts=["Delivery delayed by two weeks"],
        tone="empathetic",
    )

    assert "Acknowledge the situation" in prompt


def test_strategy_b_prompt_is_zero_shot() -> None:
    prompt = build_strategy_b_prompt(
        intent="Schedule kickoff",
        key_facts=["June 5 at 10 AM"],
        tone="formal",
    )

    assert "Schedule kickoff" in prompt
    assert "June 5 at 10 AM" in prompt
    assert "Example 1" not in prompt
    assert "professional email composer" not in prompt
    assert "Output format" in prompt


def test_strategy_b_includes_tone_guidance() -> None:
    prompt = build_strategy_b_prompt(
        intent="Deadline reminder",
        key_facts=["Due Friday"],
        tone="urgent",
    )

    assert get_tone_guidance("urgent") in prompt


def test_tone_judge_prompt_includes_rubric() -> None:
    prompt = build_tone_judge_prompt(
        tone="urgent",
        generated_email="Subject: Action Required\n\nPlease respond by Friday.",
    )

    assert "urgent" in prompt
    assert "Action Required" in prompt
    assert "SCORE:" in prompt
    assert "Scoring guide" in prompt


def test_quality_judge_prompt_includes_rubric() -> None:
    prompt = build_quality_judge_prompt(
        "Subject: Update\n\nDear team,\n\nProject is on track."
    )

    assert "GRAMMAR:" in prompt
    assert "OPENING:" in prompt
    assert "OPENING" in prompt
