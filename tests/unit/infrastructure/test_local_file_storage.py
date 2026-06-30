from app.application.services.resume_storage_service import store_resume_files
from app.infrastructure.storage.local_file_storage import LocalFileStorage


def test_local_file_storage_round_trip(tmp_path) -> None:
    from app.core.configuration import Settings

    settings = Settings(
        GOOGLE_MODEL_A="gemini-test",
        GOOGLE_MODEL_B="gemini-test",
        GOOGLE_JUDGE_MODEL="gemini-test",
        upload_dir=str(tmp_path / "uploads"),
    )
    storage = LocalFileStorage(settings)
    key = storage.put(key="test/file.pdf", data=b"%PDF-1.4 test", content_type="application/pdf")

    assert storage.exists(key)
    assert storage.get(key).startswith(b"%PDF-1.4")


def test_store_resume_files_returns_metadata(tmp_path) -> None:
    from app.core.configuration import Settings

    settings = Settings(
        GOOGLE_MODEL_A="gemini-test",
        GOOGLE_MODEL_B="gemini-test",
        GOOGLE_JUDGE_MODEL="gemini-test",
        upload_dir=str(tmp_path / "uploads"),
    )
    storage = LocalFileStorage(settings)
    stored = store_resume_files(
        file_storage=storage,
        user_id=7,
        resume_file_payloads=[("resume.pdf", b"%PDF-1.4 body")],
    )

    assert stored[0]["filename"] == "resume.pdf"
    assert stored[0]["key"].startswith("resumes/7/")
    assert storage.exists(stored[0]["key"])
