#!/usr/bin/env python3
"""Generate Final_Evaluation_Report.pdf from Final_Evaluation_Report.md."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
MD_PATH = REPORTS_DIR / "Final_Evaluation_Report.md"
PDF_PATH = REPORTS_DIR / "Final_Evaluation_Report.pdf"


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def inline_format(text: str) -> str:
    text = escape_xml(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font face='Courier' size='9'>\1</font>", text)
    return text


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontSize=22,
            leading=26,
            spaceAfter=6,
            textColor=colors.HexColor("#1a365d"),
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#4a5568"),
            spaceAfter=14,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=16,
            leading=20,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#1a365d"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#2c5282"),
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#2d3748"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            leftIndent=18,
            bulletIndent=8,
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontSize=7.5,
            leading=9.5,
            fontName="Courier",
            leftIndent=8,
            rightIndent=8,
            spaceAfter=8,
            backColor=colors.HexColor("#f7fafc"),
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontSize=9,
            leading=11,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontSize=9,
            leading=11,
        ),
    }


def parse_table(lines: list[str]) -> Table | None:
    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return None

    styles = build_styles()
    data = []
    for row_idx, row in enumerate(rows):
        style = styles["table_header"] if row_idx == 0 else styles["table_cell"]
        data.append([Paragraph(inline_format(cell), style) for cell in row])

    col_count = len(rows[0])
    available = 6.5 * inch
    col_width = available / col_count
    table = Table(data, colWidths=[col_width] * col_count, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f7fafc")],
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def parse_markdown_to_story(md_text: str) -> list:
    styles = build_styles()
    story: list = []
    lines = md_text.splitlines()
    idx = 0
    in_code = False
    code_lines: list[str] = []

    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                story.append(
                    Paragraph(
                        "<br/>".join(escape_xml(code_line) for code_line in code_lines),
                        styles["code"],
                    )
                )
                code_lines = []
                in_code = False
            else:
                in_code = True
            idx += 1
            continue

        if in_code:
            code_lines.append(line)
            idx += 1
            continue

        if stripped == "---":
            story.append(Spacer(1, 6))
            hr = HRFlowable(
                width="100%", thickness=0.5, color=colors.HexColor("#cbd5e0")
            )
            story.append(hr)
            story.append(Spacer(1, 6))
            idx += 1
            continue

        if stripped.startswith("|"):
            table_lines: list[str] = []
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                table_lines.append(lines[idx])
                idx += 1
            table = parse_table(table_lines)
            if table:
                story.append(Spacer(1, 4))
                story.append(table)
                story.append(Spacer(1, 8))
            continue

        if stripped.startswith("# "):
            story.append(Paragraph(inline_format(stripped[2:]), styles["title"]))
            idx += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(inline_format(stripped[3:]), styles["h1"]))
            idx += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(inline_format(stripped[4:]), styles["h2"]))
            idx += 1
            continue
        if stripped.startswith("#### "):
            story.append(Paragraph(inline_format(stripped[5:]), styles["h3"]))
            idx += 1
            continue

        if stripped.startswith("- "):
            bullet_text = f"• {inline_format(stripped[2:])}"
            story.append(Paragraph(bullet_text, styles["bullet"]))
            idx += 1
            continue

        is_italic = (
            stripped.startswith("*")
            and stripped.endswith("*")
            and not stripped.startswith("**")
        )
        if is_italic:
            story.append(
                Paragraph(inline_format(stripped.strip("*")), styles["subtitle"])
            )
            idx += 1
            continue

        if stripped:
            story.append(Paragraph(inline_format(stripped), styles["body"]))

        idx += 1

    return story


def add_page_number(canvas, doc):  # noqa: ARG001
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#718096"))
    page_num = f"Page {canvas.getPageNumber()}"
    canvas.drawCentredString(letter[0] / 2, 0.45 * inch, page_num)
    canvas.drawString(0.75 * inch, 0.45 * inch, "MailCraft — Final Evaluation Report")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, "June 19, 2026")
    canvas.restoreState()


def generate_pdf() -> Path:
    md_text = MD_PATH.read_text(encoding="utf-8")
    story = parse_markdown_to_story(md_text)

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="MailCraft Final Evaluation Report",
        author="MailCraft Assessment",
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return PDF_PATH


if __name__ == "__main__":
    path = generate_pdf()
    print(f"Generated: {path}")
