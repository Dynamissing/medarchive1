from __future__ import annotations

from app.services.parsers.base import DocumentParser
from app.services.parsers.docx import DocxParser
from app.services.parsers.pdf_ocr import PdfOcrCandidateParser
from app.services.parsers.pdf_text import PdfTextParser
from app.services.parsers.spreadsheet import XlsParser, XlsxParser
