"""CV upload validation + text extraction.

Validation order (matches the proposal's checklist): extension -> size -> real file signature -> readable text.
Each failure returns a distinct status/code so the UI can show a precise message.
"""
import io
import os

import docx
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from .config import settings
from .deps import error
from .utils import clean_text

ALLOWED = {".pdf", ".docx"}


def validate_and_extract(filename: str, data: bytes) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED:
        raise error(415, "UNSUPPORTED_FILE_TYPE", "Invalid file type. Please upload a PDF or DOCX file.")
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise error(413, "FILE_TOO_LARGE", f"File is larger than the {settings.max_upload_mb} MB limit.")
    if ext == ".pdf" and not data.startswith(b"%PDF-"):
        raise error(415, "INVALID_FILE_CONTENT", "This file is not a real PDF (the file signature does not match).")
    if ext == ".docx" and not data.startswith(b"PK\x03\x04"):
        raise error(415, "INVALID_FILE_CONTENT", "This file is not a real DOCX (the file signature does not match).")

    try:
        text = _extract_pdf(data) if ext == ".pdf" else _extract_docx(data)
    except Exception as exc:  # corrupted, password protected, etc.
        raise error(422, "TEXT_EXTRACTION_FAILED", "We could not read this file. Check it is not corrupted or password-protected.") from exc
    text = clean_text(text)
    if len(text) < 50:
        raise error(422, "TEXT_EXTRACTION_FAILED", "We could not find readable text. Scanned images are not supported yet.")
    return text


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise PyPdfError("encrypted")
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    lines = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            lines.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(lines)
