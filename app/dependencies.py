from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.services.llm.client import LlmClient

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


@lru_cache
def _get_llm_client_cached() -> LlmClient:
    return LlmClient(get_settings())


def get_llm_client(_: SettingsDep) -> LlmClient:
    return _get_llm_client_cached()
