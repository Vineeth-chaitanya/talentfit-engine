from pathlib import Path
from io import BytesIO
import fitz
from docx import Document
from app.core.text_cleaner import clean_text


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def load_document_from_path(path: str | Path) -> str:
    path = Path(path)
    data = path.read_bytes()
    return load_document_from_bytes(data, path.name)


def load_document_from_bytes(data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return clean_text(_read_pdf(data))
    if suffix == ".docx":
        return clean_text(_read_docx(data))
    if suffix == ".txt" or not suffix:
        return clean_text(data.decode("utf-8", errors="ignore"))
    raise ValueError(f"Unsupported file type: {suffix}. Use PDF, DOCX, or TXT.")


def _read_pdf(data: bytes) -> str:
    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    return "\n".join(pages)


def _read_docx(data: bytes) -> str:
    document = Document(BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)
