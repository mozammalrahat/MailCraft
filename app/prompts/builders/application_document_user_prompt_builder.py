"""Build user prompts for application document generation."""
# ruff: noqa: E501

from app.application.services.email_formatting_service import BODY_FORMAT_INSTRUCTIONS
from app.domain.enums.application_purpose import ApplicationPurpose
from app.domain.enums.document_type import DocumentType


def build_application_document_user_prompt(
    *,
    purpose: ApplicationPurpose,
    document_type: DocumentType,
    position_description: str,
    resume_text: str,
    grounding_links: list[str],
) -> str:
    """Assemble the user prompt for structured application document generation."""
    document_label = "email" if document_type == DocumentType.EMAIL else "cover letter"
    links_block = "\n".join(f"- {link}" for link in grounding_links) or "None provided"

    return f"""Generate a professional {document_label} for the following application context.

Purpose category: {purpose.value}
Document type: {document_type.value}

Position / job description:
{position_description}

Candidate CV content:
{resume_text}

Reference links (use Google Search to enrich context from these when helpful):
{links_block}

Return JSON with:
- subject: email subject line only (empty string for cover letters)
- body: full {document_label} text with blank lines between paragraphs
- metadata: object with generation_reason, organization, position_title, recipient_name, matched_skills (array), key_highlights_used (array), tone_used

{BODY_FORMAT_INSTRUCTIONS}
"""
