"""API dependencies for the language model client."""

from functools import lru_cache
from typing import Annotated

from app.core.configuration import Settings, get_settings
from app.infrastructure.large_language_model.client import LargeLanguageModelClient
from fastapi import Depends

SettingsDependency = Annotated[Settings, Depends(get_settings)]


@lru_cache
def _get_cached_language_model_client() -> LargeLanguageModelClient:
    return LargeLanguageModelClient(get_settings())


def get_large_language_model_client(
    _: SettingsDependency,
) -> LargeLanguageModelClient:
    """Return a shared language model client."""
    return _get_cached_language_model_client()


LargeLanguageModelClientDependency = Annotated[
    LargeLanguageModelClient, Depends(get_large_language_model_client)
]
