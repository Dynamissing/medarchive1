from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.services.parsers.base import ParserInput
from app.services.parsers.docx import DocxParser
from app.services.parsers.pdf_ocr import PdfOcrCandidateParser
from app.services.parsers.pdf_text import PdfTextParser
from app.services.parsers.spreadsheet import XlsxParser
from tests.fixtures.generators import (
    create_synthetic_docx,
    create_synthetic_scanned_pdf,
    create_synthetic_text_pdf,
    create_synthetic_xlsx,
    fake_ocr_data,
)


def test_synthetic_parser_fixtures_cover_main_formats(tmp_path: Path, monkeypatch) -> None:
    xlsx_path = create_synthetic_xlsx(tmp_path / "prices.xlsx")
    docx_path = create_synthetic_docx(tmp_path / "prices.docx")
    pdf_path = create_synthetic_text_pdf(tmp_path / "prices.pdf")
    scanned_path = create_synthetic_scanned_pdf(tmp_path / "scan.pdf")
    image = Image.new("RGB", (320, 140), "white")
    monkeypatch.setattr("app.services.parsers.pdf_ocr.convert_from_path", lambda *args, **kwargs: [image])
    monkeypatch.setattr("app.services.parsers.pdf_ocr.pytesseract.image_to_data", lambda *args, **kwargs: fake_ocr_data())

    xlsx_result = XlsxParser().parse(ParserInput(parser_format="xlsx", source_path=xlsx_path))
    docx_result = DocxParser().parse(ParserInput(parser_format="docx", source_path=docx_path))
    pdf_result = PdfTextParser().parse(ParserInput(parser_format="pdf_text", source_path=pdf_path))
    ocr_result = PdfOcrCandidateParser().parse(ParserInput(parser_format="pdf_ocr_candidate", source_path=scanned_path))

    assert xlsx_result.status == "parsed"
    assert len(xlsx_result.row_candidates) == 2
    assert docx_result.status == "parsed"
    assert docx_result.tables[0]["rows"][1]["values"] == ["A-1", "Blood test", "1000"]
    assert pdf_result.status == "parsed"
    assert any("Blood test 1000" in candidate.text for candidate in pdf_result.pdf_row_candidates)
    assert ocr_result.status == "parsed"
    assert len(ocr_result.pdf_row_candidates) == 2
