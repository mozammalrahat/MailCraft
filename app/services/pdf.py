"""Backward-compatible PDF text extraction shim."""

from app.infrastructure.document_processing.pdf_text_extractor import (
    extract_text_from_pdfs,
)

__all__ = ["extract_text_from_pdfs"]
