"""Select a file storage backend from settings."""

from app.core.configuration import Settings
from app.infrastructure.storage.base import FileStorage
from app.infrastructure.storage.local_file_storage import LocalFileStorage
from app.infrastructure.storage.s3_file_storage import S3FileStorage


def build_file_storage(settings: Settings) -> FileStorage:
    """Return the configured file storage implementation."""
    if settings.storage_backend == "s3":
        return S3FileStorage(settings)
    return LocalFileStorage(settings)
