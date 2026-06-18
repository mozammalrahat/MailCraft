from app.config import Settings


def test_settings_default_strategy_models() -> None:
    settings = Settings()
    assert settings.google_model_a == "gemini-2.0-flash"
    assert settings.google_model_b == "gemini-2.0-flash"


def test_settings_strategies_configured() -> None:
    settings = Settings(
        google_model_a="gemini-2.0-flash",
        google_model_b="gemini-2.0-flash-lite",
    )
    strategies = settings.strategies
    assert "strategy_a" in strategies
    assert "strategy_b" in strategies
    assert strategies["strategy_a"].model == "gemini-2.0-flash"
    assert strategies["strategy_b"].model == "gemini-2.0-flash-lite"
    assert strategies["strategy_a"].template == "strategy_a.jinja"
    assert strategies["strategy_b"].template == "strategy_b.jinja"
