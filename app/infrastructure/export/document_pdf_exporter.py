from datetime import UTC, datetime
from io import BytesIO

from app.database.models.generated_content import GeneratedContent
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#312e81"),
            spaceAfter=8,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4,
        ),
        "subject": ParagraphStyle(
            "Subject",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
    }


def _add_footer(canvas, doc):  # noqa: ARG001
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "MailCraft — Generated Document")
    canvas.drawCentredString(
        letter[0] / 2,
        0.45 * inch,
        f"Page {canvas.getPageNumber()}",
    )
    canvas.drawRightString(
        letter[0] - 0.75 * inch,
        0.45 * inch,
        datetime.now(UTC).strftime("%Y-%m-%d"),
    )
    canvas.restoreState()


def build_document_pdf(record: GeneratedContent) -> bytes:
    styles = _build_styles()
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"MailCraft {record.document_type or record.generation_kind}",
    )

    metadata = record.document_metadata
    document_type_label = (record.document_type or "document").replace("_", " ").title()
    purpose_label = (record.purpose or record.generation_kind).title()

    story = [
        Paragraph("MailCraft — Generated Document", styles["title"]),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1")),
        Spacer(1, 8),
        Paragraph(
            f"<b>Purpose:</b> {escape_xml(purpose_label)} &nbsp; "
            f"<b>Type:</b> {escape_xml(document_type_label)}",
            styles["meta"],
        ),
    ]

    if metadata.get("organization"):
        story.append(
            Paragraph(
                f"<b>Organization:</b> {escape_xml(str(metadata['organization']))}",
                styles["meta"],
            )
        )
    if metadata.get("position_title"):
        story.append(
            Paragraph(
                f"<b>Position:</b> {escape_xml(str(metadata['position_title']))}",
                styles["meta"],
            )
        )
    if metadata.get("recipient_name"):
        story.append(
            Paragraph(
                f"<b>Recipient:</b> {escape_xml(str(metadata['recipient_name']))}",
                styles["meta"],
            )
        )

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))

    if record.subject:
        story.append(
            Paragraph(
                f"<b>Subject:</b> {escape_xml(record.subject)}",
                styles["subject"],
            )
        )
    elif record.document_type == "cover_letter" and metadata.get("position_title"):
        story.append(
            Paragraph(
                f"<b>Re:</b> {escape_xml(str(metadata['position_title']))}",
                styles["subject"],
            )
        )

    for paragraph in record.body.split("\n\n"):
        stripped = paragraph.strip()
        if stripped:
            story.append(Paragraph(escape_xml(stripped), styles["body"]))

    pdf.build(story, onFirstPage=_add_footer, onLaterPages=_add_footer)
    return buffer.getvalue()


def pdf_filename(record: GeneratedContent) -> str:
    date_string = record.created_at.strftime("%Y%m%d")
    kind = record.purpose or record.generation_kind
    document_type = record.document_type or "content"
    return f"mailcraft-{kind}-{document_type}-{date_string}.pdf"
