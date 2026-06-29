import pytest
from app.config import get_settings
from app.db.models import init_db, reset_database_engine
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _configure_test_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("GOOGLE_MODEL_A", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_MODEL_B", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_JUDGE_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-with-enough-bytes-for-hs256-algorithm",
    )
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("HUMANIZE_CONTENT_ENABLED", "false")
    get_settings.cache_clear()
    reset_database_engine()
    init_db()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    client.post(
        "/auth/register",
        data={"email": "user@example.com", "password": "password123"},
    )
    return client
