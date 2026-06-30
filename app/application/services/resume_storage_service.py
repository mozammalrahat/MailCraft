"""Store uploaded resume PDFs when persistence is enabled."""

import uuid

from app.infrastructure.storage.base import FileStorage


def build_resume_storage_key(*, user_id: int, filename: str) -> str:
    """Build a user-scoped storage key for a resume PDF."""
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"resumes/{user_id}/{uuid.uuid4().hex}/{safe_name}"


def store_resume_files(
    *,
    file_storage: FileStorage,
    user_id: int,
    resume_file_payloads: list[tuple[str, bytes]],
) -> list[dict[str, str]]:
    """Persist resume PDF bytes and return filename/key metadata."""
    stored: list[dict[str, str]] = []
    for filename, content in resume_file_payloads:
        key = build_resume_storage_key(user_id=user_id, filename=filename)
        file_storage.put(
            key=key,
            data=content,
            content_type="application/pdf",
        )
        stored.append({"filename": filename, "key": key})
    return stored
