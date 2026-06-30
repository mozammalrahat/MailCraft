"""File storage dependency injection."""

from typing import Annotated

from app.core.configuration import Settings, get_settings
from app.infrastructure.storage.base import FileStorage
from app.infrastructure.storage.factory import build_file_storage
from fastapi import Depends

_storage_cache: dict[tuple[str, ...], FileStorage] = {}


def _settings_cache_key(settings: Settings) -> tuple[str, ...]:
    return (
        settings.storage_backend,
        settings.upload_dir,
        settings.s3_bucket,
        settings.aws_region,
        settings.aws_endpoint_url,
    )


def get_file_storage(settings: Settings = Depends(get_settings)) -> FileStorage:  # noqa: B008
    """Return a cached file storage client for the active settings."""
    cache_key = _settings_cache_key(settings)
    cached = _storage_cache.get(cache_key)
    if cached is not None:
        return cached
    storage = build_file_storage(settings)
    _storage_cache[cache_key] = storage
    return storage


FileStorageDependency = Annotated[FileStorage, Depends(get_file_storage)]
