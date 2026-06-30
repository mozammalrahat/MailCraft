from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_generate_email_api_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/emails/generate",
        json={
            "intent": "Follow up after product demo",
            "key_facts": ["Demo held on May 12"],
            "tone": "formal",
        },
    )
    assert response.status_code == 401


def test_generate_email_api_success(authenticated_client: TestClient) -> None:
    mock_response = (
        "Subject: Demo Follow-Up\n\nThank you for attending the demo held on May 12."
    )

    with patch(
        "app.infrastructure.large_language_model.client.LargeLanguageModelClient.generate_content",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = authenticated_client.post(
            "/api/emails/generate",
            json={
                "intent": "Follow up after product demo",
                "key_facts": ["Demo held on May 12"],
                "tone": "formal",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["email"]
    assert data["subject"] == "Demo Follow-Up"
    assert data["strategy"] == "strategy_a"
    assert data["prompt_version"] == "2.0.0"
    assert data["model"]
    assert data["generated_content_id"] is not None


def test_generate_email_api_validation_error(authenticated_client: TestClient) -> None:
    response = authenticated_client.post(
        "/api/emails/generate",
        json={
            "intent": "Test",
            "key_facts": [],
            "tone": "formal",
        },
    )

    assert response.status_code == 422


def test_generate_email_api_missing_api_key(authenticated_client: TestClient) -> None:
    from app.api.dependencies.large_language_model import (
        get_large_language_model_client,
    )
    from app.core.configuration import Settings, get_settings
    from app.infrastructure.large_language_model.client import LargeLanguageModelClient
    from app.main import app

    test_settings = Settings(
        google_api_key="",
        GOOGLE_MODEL_A="gemini-2.5-flash",
        GOOGLE_MODEL_B="gemini-2.5-flash",
        GOOGLE_JUDGE_MODEL="gemini-2.5-flash",
    )
    mock_client = LargeLanguageModelClient(test_settings)
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_large_language_model_client] = lambda: mock_client
    get_settings.cache_clear()

    try:
        response = authenticated_client.post(
            "/api/emails/generate",
            json={
                "intent": "Test intent",
                "key_facts": ["Fact one"],
                "tone": "casual",
            },
        )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()

    assert response.status_code == 502
    assert "API key" in response.json()["detail"]
