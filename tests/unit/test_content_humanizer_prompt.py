from app.prompts.templates.content_humanizer import CONTENT_HUMANIZER_SYSTEM_RULES


def test_banned_words_exclude_common_professional_english() -> None:
    common_words = [
        "can",
        "may",
        "just",
        "very",
        "really",
        "could",
        "maybe",
        "however",
    ]
    for word in common_words:
        assert f"{word}," not in CONTENT_HUMANIZER_SYSTEM_RULES


def test_banned_words_keep_ai_telltale_terms() -> None:
    assert "delve" in CONTENT_HUMANIZER_SYSTEM_RULES
    assert "pivotal" in CONTENT_HUMANIZER_SYSTEM_RULES
