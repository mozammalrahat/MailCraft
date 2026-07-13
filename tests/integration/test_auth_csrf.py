"""HTML auth flows with CSRF protection enabled."""

from collections.abc import Iterator

import pytest
from app.core.configuration import get_settings
from app.database.engine_manager import initialize_database, reset_database_engine
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def csrf_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Iterator[TestClient]:
    db_file = tmp_path / "csrf-auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("GOOGLE_MODEL_A", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_MODEL_B", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_JUDGE_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-secret-key-with-enough-bytes-for-hs256-algorithm",
    )
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("HUMANIZE_CONTENT_ENABLED", "false")
    get_settings.cache_clear()
    reset_database_engine()
    initialize_database()
    with TestClient(create_app()) as client:
        yield client


def test_html_login_with_csrf_succeeds(csrf_client: TestClient) -> None:
    login_page = csrf_client.get("/auth/login")
    assert login_page.status_code == 200
    csrf_token = csrf_client.cookies.get("csrf_token")
    assert csrf_token

    register = csrf_client.post(
        "/auth/register",
        data={
            "email": "csrf-user@example.com",
            "password": "password123",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert register.status_code == 303, register.text

    csrf_client.post("/auth/logout", follow_redirects=False)
    csrf_token = csrf_client.cookies.get("csrf_token")
    assert csrf_token

    login = csrf_client.post(
        "/auth/login",
        data={
            "email": "csrf-user@example.com",
            "password": "password123",
            "csrf_token": csrf_token,
        },
        follow_redirects=False,
    )
    assert login.status_code == 303, login.text
    assert login.headers["location"] == "/dashboard"
