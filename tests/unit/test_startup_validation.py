import pytest
from app.core.configuration import Settings
from app.core.startup_validation import validate_production_settings


def test_weak_jwt_rejected_when_not_debug() -> None:
    settings = Settings(
        debug=False,
        jwt_secret_key="change-me-in-production",
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
        google_api_key="test-key",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        validate_production_settings(settings)


def test_short_jwt_rejected_when_not_debug() -> None:
    settings = Settings(
        debug=False,
        jwt_secret_key="too-short",
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
        google_api_key="test-key",
    )
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        validate_production_settings(settings)


def test_missing_api_key_rejected_when_not_debug() -> None:
    settings = Settings(
        debug=False,
        jwt_secret_key="a" * 32,
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
        google_api_key="",
    )
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        validate_production_settings(settings)


def test_strong_settings_pass_when_not_debug() -> None:
    settings = Settings(
        debug=False,
        jwt_secret_key="a" * 32,
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
        google_api_key="test-key",
    )
    validate_production_settings(settings)


def test_weak_jwt_allowed_when_debug() -> None:
    settings = Settings(
        debug=True,
        jwt_secret_key="change-me-in-production",
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
    )
    validate_production_settings(settings)
