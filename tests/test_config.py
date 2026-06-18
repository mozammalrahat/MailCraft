from app.config import Settings


def test_settings_reads_models_from_env() -> None:
    settings = Settings()
    assert settings.google_model_a == "gemini-2.5-flash"
    assert settings.google_model_b == "gemini-2.5-flash"
    assert settings.google_judge_model == "gemini-2.5-flash"


def test_settings_strategies_use_env_models() -> None:
    settings = Settings(
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash-lite",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
    )
    strategies = settings.strategies
    assert strategies["strategy_a"].model == "gemini-2.5-flash"
    assert strategies["strategy_b"].model == "gemini-2.5-flash-lite"


def test_settings_env_override(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_MODEL_A", "gemini-2.5-pro")
    monkeypatch.setenv("GOOGLE_MODEL_B", "gemini-2.5-flash-lite")
    monkeypatch.setenv("GOOGLE_JUDGE_MODEL", "gemini-2.5-flash")

    settings = Settings()

    assert settings.google_model_a == "gemini-2.5-pro"
    assert settings.google_model_b == "gemini-2.5-flash-lite"
    assert settings.google_judge_model == "gemini-2.5-flash"
