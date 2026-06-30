"""File storage protocol and factory."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class FileStorage(Protocol):
    """Store and retrieve binary upload payloads."""

    def put(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Persist data and return the storage key."""

    def get(self, key: str) -> bytes:
        """Load data for a storage key."""

    def delete(self, key: str) -> None:
        """Remove a stored object."""

    def exists(self, key: str) -> bool:
        """Return whether the key exists."""
