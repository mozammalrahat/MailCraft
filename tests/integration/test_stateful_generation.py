from io import BytesIO
from unittest.mock import AsyncMock, patch

from app.db.models import Scenario, get_session_factory
from reportlab.pdfgen import canvas


def _minimal_pdf(text: str = "Jane Doe — Python, ML, 5 years experience.") -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def _register(client) -> None:
    client.post(
        "/auth/register",
        data={"email": "gen@example.com", "password": "password123"},
        follow_redirects=False,
    )


def test_create_generation_persists_document(client) -> None:
    _register(client)

    factory = get_session_factory()
    db = factory()
    try:
        scenario = (
            db.query(Scenario)
            .filter(Scenario.purpose == "interview", Scenario.document_type == "email")
            .first()
        )
        assert scenario is not None
        scenario_id = scenario.id
    finally:
        db.close()

    mock_payload = {
        "subject": "Application for ML Engineer",
        "body": "Dear Hiring Manager,\n\nI am excited to apply.",
        "metadata": {
            "generation_reason": "Job application",
            "organization": "Acme Corp",
            "position_title": "ML Engineer",
            "recipient_name": "Hiring Manager",
            "matched_skills": ["Python"],
            "key_highlights_used": ["5 years experience"],
            "tone_used": "formal",
        },
    }

    with patch(
        "app.infrastructure.large_language_model.client.LargeLanguageModelClient.generate_structured_with_grounding",
        new_callable=AsyncMock,
        return_value=(mock_payload, {"web_search_queries": ["Acme Corp careers"]}),
    ):
        response = client.post(
            "/api/generations",
            data={
                "purpose": "interview",
                "document_type": "email",
                "scenario_id": str(scenario_id),
                "position_description": "We are hiring an ML Engineer at Acme Corp.",
                "grounding_links": "https://acme.example/jobs/ml",
            },
            files=[("resume_files", ("resume.pdf", _minimal_pdf(), "application/pdf"))],
        )

    assert response.status_code == 201
    data = response.json()
    assert data["subject"] == mock_payload["subject"]
    assert data["metadata_json"]["organization"] == "Acme Corp"

    pdf_response = client.get(f"/api/generations/{data['id']}/pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert pdf_response.content.startswith(b"%PDF")
