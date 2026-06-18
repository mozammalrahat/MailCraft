import pytest
from app.config import get_settings
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _configure_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_MODEL_A", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_MODEL_B", "gemini-2.5-flash")
    monkeypatch.setenv("GOOGLE_JUDGE_MODEL", "gemini-2.5-flash")
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
