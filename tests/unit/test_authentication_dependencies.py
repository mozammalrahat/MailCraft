"""Authentication dependency tests."""

import pytest
from app.core.configuration import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def unauthenticated_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    db_file = tmp_path / "auth-deps.db"
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("GOOGLE_MODEL_A", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_MODEL_B", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_JUDGE_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("HUMANIZE_CONTENT_ENABLED", "false")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_dashboard_redirects_without_cookie(unauthenticated_client: TestClient) -> None:
    response = unauthenticated_client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"
