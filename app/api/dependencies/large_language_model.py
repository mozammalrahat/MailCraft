"""API dependencies for the language model client."""

from typing import Annotated

from app.core.configuration import Settings, get_settings
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from fastapi import Depends

SettingsDependency = Annotated[Settings, Depends(get_settings)]

_client_cache: dict[tuple[str, ...], LargeLanguageModelClient] = {}


def _settings_cache_key(settings: Settings) -> tuple[str, ...]:
    return (
        settings.google_api_key,
        settings.google_model_a,
        settings.google_judge_model,
        str(settings.llm_request_delay_seconds),
        str(settings.llm_max_retries),
        str(settings.llm_retry_base_delay_seconds),
        str(settings.llm_retry_max_delay_seconds),
    )


def get_large_language_model_client(
    settings: SettingsDependency,
) -> LargeLanguageModelClient:
    """Return a shared language model client for the active settings."""
    cache_key = _settings_cache_key(settings)
    cached = _client_cache.get(cache_key)
    if cached is not None:
        return cached
    client = LargeLanguageModelClient(settings)
    _client_cache[cache_key] = client
    return client


LargeLanguageModelClientDependency = Annotated[
    LargeLanguageModelClient, Depends(get_large_language_model_client)
]
