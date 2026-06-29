from app.services.email.formatting import (
    build_clipboard_text,
    format_document_body,
    resolve_subject_and_body,
)


def test_format_single_line_email_into_paragraphs() -> None:
    body = (
        "Dear Hiring Manager, I am writing to express my interest in the ML Engineer role. "
        "I have five years of Python experience and published work at NeurIPS. "
        "I would welcome the chance to discuss my fit for your team. "
        "Best regards, Jane Doe"
    )
    formatted = format_document_body(body)
    assert formatted.startswith("Dear Hiring Manager,")
    assert "\n\n" in formatted
    assert formatted.endswith("Jane Doe")
    assert "Best regards," in formatted


def test_resolve_subject_strips_duplicate_subject_line() -> None:
    subject, body = resolve_subject_and_body(
        "Subject: Application for ML Engineer\n\nDear team,\n\nHello.",
        None,
    )
    assert subject == "Application for ML Engineer"
    assert body.startswith("Dear team,")
    assert "Subject:" not in body


def test_build_clipboard_text_includes_subject() -> None:
    text = build_clipboard_text(
        subject="Application for ML Engineer",
        body="Dear Hiring Manager,\n\nI am interested in the role.\n\nBest regards,\nJane",
    )
    assert text.startswith("Subject: Application for ML Engineer\n\n")
    assert "Dear Hiring Manager," in text


def test_preserves_existing_paragraph_breaks() -> None:
    body = "Dear Dr. Smith,\n\nI am applying to your lab.\n\nBest regards,\nJane"
    assert format_document_body(body) == body
