from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.parsers.base import ParserInput
from app.services.parsers.pdf_text import PdfTextParser


def create_text_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.drawString(72, 740, "Clinic price list")
    pdf.drawString(72, 710, "001 Consultation cardiologist 500")
    pdf.drawString(72, 690, "002 Ultrasound abdominal")
    pdf.drawString(260, 690, "1200")
    pdf.drawString(72, 670, "003 Complex laboratory package")
    pdf.drawString(72, 654, "with extended biomarkers 2500")
    pdf.showPage()
    pdf.drawString(72, 740, "004 Multi page service name")
    pdf.showPage()
    pdf.drawString(72, 740, "continued variant 3300")
    pdf.save()


def test_pdf_text_parser_extracts_raw_pages_rows_and_locators(tmp_path: Path) -> None:
    pdf_path = tmp_path / "clinic.pdf"
    create_text_pdf(pdf_path)

    result = PdfTextParser().parse(ParserInput(parser_format="pdf_text", source_path=pdf_path))

    assert result.status == "parsed"
    assert result.parser_format == "pdf_text"
    assert result.metadata["page_count"] == 3
    assert result.metadata["confidence"] > 0
    assert "Clinic price list" in result.extracted_text
    assert result.metadata["page_text"][0]["page_number"] == 1
    assert "Consultation cardiologist" in result.metadata["page_text"][0]["text"]
    assert len(result.pdf_row_candidates) >= 4

    first = result.pdf_row_candidates[0]
    assert first.page_number == 1
    assert first.locator == "page:1:row:2"
    assert first.values["code"] == "001"
    assert first.values["price"] == "500"
    assert first.confidence > 0.8


def test_pdf_text_parser_handles_fragmented_wrapped_and_multipage_lines(tmp_path: Path) -> None:
    pdf_path = tmp_path / "fragmented.pdf"
    create_text_pdf(pdf_path)

    result = PdfTextParser().parse(ParserInput(parser_format="pdf_text", source_path=pdf_path))
    texts = [candidate.text for candidate in result.pdf_row_candidates]

    assert any("Ultrasound abdominal 1200" in text for text in texts)
    assert any("Complex laboratory package with extended biomarkers 2500" in text for text in texts)
    assert any("Multi page service name continued variant 3300" in text for text in texts)
    assert all(candidate.locator.startswith("page:") for candidate in result.pdf_row_candidates)
