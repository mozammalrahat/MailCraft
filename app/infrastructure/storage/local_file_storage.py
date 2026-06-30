"""Local filesystem object storage."""

from pathlib import Path

from app.core.configuration import Settings


class LocalFileStorage:
    """Persist uploads under the configured upload directory."""

    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.upload_dir)

    def put(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        del content_type
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def get(self, key: str) -> bytes:
        return (self._root / key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._root / key
        if path.exists():
            path.unlink()

    def exists(self, key: str) -> bool:
        return (self._root / key).is_file()
