"""Shared helpers for constructing Settings instances in tests."""

from typing import Any

from app.core.configuration import Settings

_DEFAULT_TEST_SETTINGS: dict[str, Any] = {
    "google_api_key": "test-key",
    "google_model_a": "gemini-test",
    "google_model_b": "gemini-test",
    "google_judge_model": "gemini-test",
}


def build_test_settings(**overrides: Any) -> Settings:
    """Build Settings with stable test defaults and optional overrides."""
    return Settings(**{**_DEFAULT_TEST_SETTINGS, **overrides})
