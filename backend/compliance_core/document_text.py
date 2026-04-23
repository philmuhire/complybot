from io import BytesIO

from docx import Document
from pypdf import PdfReader

_MAX_BYTES = 12 * 1024 * 1024


def _ensure_size(data: bytes) -> None:
    if len(data) > _MAX_BYTES:
        msg = f"file too large (max {_MAX_BYTES} bytes)"
        raise ValueError(msg)


def text_from_bytes(filename: str, data: bytes) -> str:
    _ensure_size(data)
    name = (filename or "upload").lower()
    if name.endswith(".pdf"):
        r = PdfReader(BytesIO(data))
        return "\n\n".join(
            p.extract_text() or "" for p in r.pages
        ).strip()
    if name.endswith(".docx"):
        d = Document(BytesIO(data))
        return "\n\n".join(p.text for p in d.paragraphs if p.text).strip()
    if name.endswith(".txt") or "." not in name:
        return data.decode("utf-8", errors="replace").strip()
    msg = f"unsupported file type: {filename!r} (use .pdf, .docx, or .txt)"
    raise ValueError(msg)
