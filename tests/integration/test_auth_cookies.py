"""Authentication cookie security tests."""

import pytest
from app.core.configuration import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def production_auth_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    db_file = tmp_path / "auth-cookies.db"
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("GOOGLE_API_KEY", "test-production-key")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "production-secret-key-with-enough-bytes-for-hs256",
    )
    monkeypatch.setenv("GOOGLE_MODEL_A", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_MODEL_B", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_JUDGE_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("HUMANIZE_CONTENT_ENABLED", "false")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_register_sets_secure_cookies(production_auth_client: TestClient) -> None:
    response = production_auth_client.post(
        "/api/auth/register",
        json={"email": "secure@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert len(set_cookie_headers) == 2
    combined = " ".join(set_cookie_headers).lower()
    assert "httponly" in combined
    assert "secure" in combined
    assert "path=/" in combined
    assert "samesite=lax" in combined


def test_logout_clears_auth_cookies(production_auth_client: TestClient) -> None:
    production_auth_client.post(
        "/api/auth/register",
        json={"email": "logout@example.com", "password": "password123"},
    )
    response = production_auth_client.post("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    set_cookie_headers = response.headers.get_list("set-cookie")
    combined = " ".join(set_cookie_headers).lower()
    assert "access_token=" in combined
    assert "refresh_token=" in combined
    assert "max-age=0" in combined or '=""' in combined
