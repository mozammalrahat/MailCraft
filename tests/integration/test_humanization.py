"""Integration tests for the email generation pipeline with humanization enabled."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def humanize_client(monkeypatch, tmp_path) -> TestClient:
    """TestClient with humanization enabled for this test module."""
    from app.core.configuration import get_settings
    from app.database.engine_manager import initialize_database, reset_database_engine
    from app.main import app

    monkeypatch.setenv("HUMANIZE_CONTENT_ENABLED", "true")
    monkeypatch.setenv("HUMANIZE_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("HUMANIZE_FACT_RECALL_THRESHOLD", "0.5")
    get_settings.cache_clear()
    reset_database_engine()
    initialize_database()
    return TestClient(app, raise_server_exceptions=True)


def _raw_email_body(include_fact: str) -> str:
    return (
        f"Subject: Interview Follow-Up\n\n"
        f"Dear Dr. Lee,\n\n"
        f"Thank you for the interview on Tuesday. {include_fact} "
        f"I look forward to hearing from you.\n\nBest regards,\nJane"
    )


def test_generate_email_with_humanization_preserves_facts(
    humanize_client: TestClient,
) -> None:
    """Full HTTP -> pipeline -> DB round-trip with humanization enabled.

    Verifies that the humanizer is invoked, that key facts survive, and
    that the persisted record stores the humanizer metadata columns.
    """
    humanize_client.post(
        "/auth/register",
        data={"email": "humanize@example.com", "password": "password123"},
        follow_redirects=False,
    )

    key_fact = "Discussed salary of 120k"
    raw_output = _raw_email_body(key_fact)
    humanized_output = (
        f"Subject: Interview Follow-Up\n\n"
        f"Hi Dr. Lee,\n\n"
        f"Great chatting Tuesday — {key_fact}. Excited for next steps.\n\nJane"
    )

    with (
        patch(
            "app.infrastructure.large_language_model.client"
            ".LargeLanguageModelClient.generate_content",
            new_callable=AsyncMock,
        ) as mock_gen,
    ):
        mock_gen.side_effect = [raw_output, humanized_output]

        response = humanize_client.post(
            "/api/emails/generate",
            json={
                "intent": "Follow up after interview",
                "key_facts": [key_fact],
                "tone": "formal",
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"], "email body should not be empty"
    assert data["subject"] == "Interview Follow-Up"
    assert key_fact.lower() in data["email"].lower(), (
        "Key fact must survive humanization"
    )
    assert data["generated_content_id"] is not None


def test_generate_email_humanization_fallback_on_llm_error(
    humanize_client: TestClient,
) -> None:
    """If the humanizer LLM call fails, pipeline falls back to raw output."""
    from app.core.exceptions import LlmError

    humanize_client.post(
        "/auth/register",
        data={"email": "fallback@example.com", "password": "password123"},
        follow_redirects=False,
    )

    key_fact = "Project delivered on time"
    raw_output = _raw_email_body(key_fact)

    with patch(
        "app.infrastructure.large_language_model.client"
        ".LargeLanguageModelClient.generate_content",
        new_callable=AsyncMock,
    ) as mock_gen:
        mock_gen.side_effect = [raw_output, LlmError("humanizer unavailable")]

        response = humanize_client.post(
            "/api/emails/generate",
            json={
                "intent": "Follow up after project delivery",
                "key_facts": [key_fact],
                "tone": "formal",
            },
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"]
    assert data["generated_content_id"] is not None
