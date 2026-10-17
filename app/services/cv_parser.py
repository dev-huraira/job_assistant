import io
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.core.logging_config import get_logger

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class CVParsingError(Exception):
    """Raised when a CV file cannot be read or parsed."""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from PDF file bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))

    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages_text).strip()

    if not text:
        raise CVParsingError(
            "No extractable text found in PDF (it may be a scanned image "
            "with no text layer)."
        )
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX file bytes."""
    document = Document(io.BytesIO(file_bytes))

    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()

    if not text:
        raise CVParsingError("No extractable text found in DOCX file.")
    return text


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract plain text from a .txt file's bytes."""
    text = file_bytes.decode("utf-8", errors="ignore").strip()

    if not text:
        raise CVParsingError("Text file is empty.")
    return text


def extract_cv_text(filename: str, file_bytes: bytes) -> str:
    """Detect file type by extension and extract plain CV text from it.

    Args:
        filename: the original filename (used only to read its extension).
        file_bytes: the raw file content.

    Returns:
        The extracted plain text.

    Raises:
        CVParsingError: if the file is too large, an unsupported type,
            or contains no extractable text.
    """
    logger.info("Extracting CV text from file: %s (%d bytes)", filename, len(file_bytes))

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise CVParsingError(
            f"File too large ({len(file_bytes)} bytes). "
            f"Max allowed is {MAX_FILE_SIZE_BYTES} bytes."
        )

    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise CVParsingError(
            f"Unsupported file type '{extension}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if extension == ".pdf":
        text = extract_text_from_pdf(file_bytes)
    elif extension == ".docx":
        text = extract_text_from_docx(file_bytes)
    else:
        text = extract_text_from_txt(file_bytes)

    logger.info("Extracted %d characters from %s", len(text), filename)
    return text