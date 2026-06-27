from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileTypeDetection:
    extension: str | None
    mime_type: str | None
    parser_format: str | None
    pdf_text_available: bool | None = None


def detect_file_type(
    filename: str,
    mime_type: str | None = None,
    path: Path | None = None,
) -> FileTypeDetection:
    extension = Path(filename).suffix.casefold() or None
    guessed_mime, _encoding = mimetypes.guess_type(filename)
    resolved_mime = mime_type or guessed_mime

    parser_format: str | None = None
    pdf_text_available: bool | None = None
    if extension == ".xlsx":
        parser_format = "xlsx"
    elif extension == ".xls":
        parser_format = "xls"
    elif extension == ".docx":
        parser_format = "docx"
    elif extension == ".pdf" or resolved_mime == "application/pdf":
        pdf_text_available = has_pdf_text_markers(path) if path is not None else False
        parser_format = "pdf_text" if pdf_text_available else "pdf_ocr_candidate"

    return FileTypeDetection(
        extension=extension,
        mime_type=resolved_mime,
        parser_format=parser_format,
        pdf_text_available=pdf_text_available,
    )


def has_pdf_text_markers(path: Path, read_limit: int = 1024 * 256) -> bool:
    try:
        with path.open("rb") as file_obj:
            sample = file_obj.read(read_limit)
    except OSError:
        return False

    markers = (b" BT", b"\nBT", b"/Font", b"Tj", b"TJ")
    return any(marker in sample for marker in markers)
