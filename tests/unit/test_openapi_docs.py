"""OpenAPI documentation availability tests."""

import pytest
from app.core.configuration import get_settings
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def production_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-production-key")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "production-secret-key-with-enough-bytes-for-hs256",
    )
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("RUN_MIGRATIONS_ON_STARTUP", "false")
    get_settings.cache_clear()
    return TestClient(create_app())


@pytest.fixture
def debug_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("RUN_MIGRATIONS_ON_STARTUP", "false")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_openapi_docs_disabled_in_production(production_client: TestClient) -> None:
    assert production_client.get("/docs").status_code == 404
    assert production_client.get("/redoc").status_code == 404
    assert production_client.get("/openapi.json").status_code == 404


def test_openapi_docs_enabled_in_debug(debug_client: TestClient) -> None:
    assert debug_client.get("/docs").status_code == 200
    assert debug_client.get("/redoc").status_code == 200
    assert debug_client.get("/openapi.json").status_code == 200
