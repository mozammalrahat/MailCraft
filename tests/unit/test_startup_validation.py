import pytest
from app.core.startup_validation import validate_production_settings

from tests.support.settings_factory import build_test_settings


def test_weak_jwt_rejected_when_not_debug() -> None:
    settings = build_test_settings(
        debug=False,
        jwt_secret_key="change-me-in-production",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        validate_production_settings(settings)


def test_short_jwt_rejected_when_not_debug() -> None:
    settings = build_test_settings(
        debug=False,
        jwt_secret_key="too-short",
    )
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        validate_production_settings(settings)


def test_missing_api_key_rejected_when_not_debug() -> None:
    settings = build_test_settings(
        debug=False,
        jwt_secret_key="a" * 32,
        google_api_key="",
    )
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        validate_production_settings(settings)


def test_strong_settings_pass_when_not_debug() -> None:
    settings = build_test_settings(
        debug=False,
        jwt_secret_key="a" * 32,
    )
    validate_production_settings(settings)


def test_weak_jwt_allowed_when_debug() -> None:
    settings = build_test_settings(
        debug=True,
        jwt_secret_key="change-me-in-production",
    )
    validate_production_settings(settings)
