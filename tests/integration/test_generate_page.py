from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


def test_generate_page_requires_auth(client: TestClient) -> None:
    response = client.get("/generate", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"


def test_generate_page_renders(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/generate")
    assert response.status_code == 200
    assert "Generate Email" in response.text
    assert 'name="intent"' in response.text
    assert 'name="key_facts"' in response.text


def test_generate_page_post_success(authenticated_client: TestClient) -> None:
    mock_response = (
        "Subject: Sprint Update\n\nSprint ends Friday and migration is 80% complete."
    )

    with patch(
        "app.infrastructure.large_language_model.client.LargeLanguageModelClient.generate_content",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = authenticated_client.post(
            "/generate",
            data={
                "intent": "Share sprint progress",
                "key_facts": ["Sprint ends Friday", "Migration is 80% complete"],
                "tone": "casual",
                "strategy": "strategy_a",
            },
        )

    assert response.status_code == 200
    assert "Sprint Update" in response.text
    assert "Generated Email" in response.text
    assert "Saved to history" in response.text


def test_generate_page_post_validation_error(authenticated_client: TestClient) -> None:
    response = authenticated_client.post(
        "/generate",
        data={
            "intent": "Test",
            "key_facts": "   ",
            "tone": "formal",
        },
    )

    assert response.status_code == 200
    assert "At least one key fact is required" in response.text
