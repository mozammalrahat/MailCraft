"""Backward-compatible FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from app.api.dependencies.large_language_model import (
    LargeLanguageModelClientDependency,
    get_large_language_model_client,
)
from app.core.configuration import Settings, get_settings
from app.infrastructure.large_language_model.client import LlmClient

SettingsDep = Annotated[Settings, Depends(get_settings)]
LlmClientDep = LargeLanguageModelClientDependency
LlmDep = LlmClientDep


def get_llm_client(settings: SettingsDep) -> LlmClient:
    """Return shared language model client (backward-compatible)."""
    return get_large_language_model_client(settings)


__all__ = ["get_llm_client", "get_settings", "LlmClientDep", "LlmDep", "SettingsDep"]
