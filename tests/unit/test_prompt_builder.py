from app.schemas.email import EmailGenerationRequest


def _sample_request() -> EmailGenerationRequest:
    return EmailGenerationRequest(
        intent="Schedule a project kickoff meeting",
        key_facts=[
            "Kickoff proposed for June 5 at 10 AM",
            "Attendees: product, engineering, and design leads",
        ],
        tone="formal",
    )


def test_build_prompt_includes_all_inputs_strategy_a() -> None:
    from app.services.email.prompt_builder import build_prompt

    request = _sample_request()
    prompt = build_prompt(request, strategy="strategy_a")

    assert request.intent in prompt
    assert request.key_facts[0] in prompt
    assert request.key_facts[1] in prompt
    assert request.tone in prompt


def test_build_prompt_includes_all_inputs_strategy_b() -> None:
    from app.services.email.prompt_builder import build_prompt

    request = _sample_request()
    prompt = build_prompt(request, strategy="strategy_b")

    assert request.intent in prompt
    assert request.key_facts[0] in prompt
    assert request.key_facts[1] in prompt
    assert request.tone in prompt


def test_strategy_a_includes_few_shot_examples() -> None:
    from app.services.email.prompt_builder import build_prompt

    request = _sample_request()
    prompt = build_prompt(request, strategy="strategy_a")

    assert "Example 1" in prompt
    assert "Example 4" in prompt
    assert "professional email composer" in prompt


def test_strategy_b_is_zero_shot_baseline() -> None:
    from app.services.email.prompt_builder import build_prompt

    request = _sample_request()
    prompt = build_prompt(request, strategy="strategy_b")

    assert "Example 1" not in prompt
    assert "senior B2B email copywriter" not in prompt
    assert "professional email composer" not in prompt


def test_unsupported_strategy_raises() -> None:
    import pytest
    from app.services.email.prompt_builder import build_prompt

    request = _sample_request()

    with pytest.raises(ValueError, match="Unsupported strategy"):
        build_prompt(request, strategy="strategy_c")
