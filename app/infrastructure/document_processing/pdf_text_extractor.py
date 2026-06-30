from io import BytesIO

from app.core.configuration import Settings
from app.core.exceptions import ServiceValidationError
from pypdf import PdfReader

_PDF_MAGIC = b"%PDF-"


def _validate_pdf_content(filename: str, content: bytes) -> None:
    if not content.startswith(_PDF_MAGIC):
        raise ServiceValidationError(f"Invalid PDF file (magic bytes): {filename}")


def extract_text_from_pdfs(
    files: list[tuple[str, bytes]],
    *,
    settings: Settings,
) -> tuple[str, list[str]]:
    if not files:
        raise ServiceValidationError("At least one CV/resume PDF is required")

    max_bytes = settings.upload_max_mb * 1024 * 1024
    filenames: list[str] = []
    sections: list[str] = []

    for filename, content in files:
        if not filename.lower().endswith(".pdf"):
            raise ServiceValidationError(f"Only PDF files are supported: {filename}")
        if len(content) > max_bytes:
            raise ServiceValidationError(
                f"File too large (max {settings.upload_max_mb}MB): {filename}"
            )

        _validate_pdf_content(filename, content)

        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
        if not text:
            raise ServiceValidationError(f"Could not extract text from: {filename}")

        filenames.append(filename)
        sections.append(f"--- CV: {filename} ---\n{text}")

    return "\n\n".join(sections), filenames
