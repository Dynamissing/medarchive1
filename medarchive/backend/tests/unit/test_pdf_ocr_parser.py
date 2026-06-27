from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.parsers.base import ParserInput
from app.services.parsers.pdf_ocr import PdfOcrCandidateParser, is_ocr_candidate_pdf


def create_image_only_pdf(path: Path) -> None:
    image_path = path.with_suffix(".png")
    image = Image.new("RGB", (300, 120), "white")
    image.save(image_path)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pdf.drawImage(str(image_path), 72, 600, width=300, height=120)
    pdf.save()


def fake_ocr_data(confidence: int = 92) -> dict[str, list]:
    words = ["001", "Консультация", "терапевта", "500", "002", "MRI", "1200"]
    return {
        "text": words,
        "conf": [confidence, confidence, confidence, confidence, 40, 40, 40],
        "left": [10, 45, 170, 280, 10, 45, 150],
        "block_num": [1, 1, 1, 1, 1, 1, 1],
        "par_num": [1, 1, 1, 1, 1, 1, 1],
        "line_num": [1, 1, 1, 1, 2, 2, 2],
    }


def test_pdf_ocr_parser_extracts_rows_artifacts_and_low_confidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = tmp_path / "scan.pdf"
    create_image_only_pdf(pdf_path)
    image = Image.new("RGB", (200, 100), "white")
    monkeypatch.setattr("app.services.parsers.pdf_ocr.convert_from_path", lambda *args, **kwargs: [image])
    monkeypatch.setattr("app.services.parsers.pdf_ocr.pytesseract.image_to_data", lambda *args, **kwargs: fake_ocr_data())

    result = PdfOcrCandidateParser().parse(ParserInput(parser_format="pdf_ocr_candidate", source_path=pdf_path))

    assert result.status == "parsed"
    assert result.parser_format == "pdf_ocr_candidate"
    assert result.metadata["ocr_candidate"] is True
    assert result.metadata["page_text"][0]["ocr_confidence"] == 0.697
    assert result.metadata["page_text"][0]["artifact"]["engine"] == "tesseract"
    assert result.metadata["page_text"][0]["artifact"]["languages"] == "rus+kaz+eng"
    assert result.metadata["page_text"][0]["artifact"]["line_confidences"] == [0.92, 0.4]
    assert "001 Консультация терапевта 500" in result.extracted_text
    assert len(result.pdf_row_candidates) == 2
    assert result.pdf_row_candidates[0].values["price"] == "500"
    assert result.pdf_row_candidates[0].low_confidence is False
    assert result.pdf_row_candidates[1].values["price"] == "1200"
    assert result.pdf_row_candidates[1].low_confidence is True
    assert "One or more OCR row candidates were marked low confidence." in result.warnings


def test_ocr_candidate_detection_marks_image_only_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "image-only.pdf"
    create_image_only_pdf(pdf_path)

    assert is_ocr_candidate_pdf(pdf_path) is True


def test_pdf_ocr_parser_returns_failed_result_when_local_tools_fail(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf_path = tmp_path / "scan.pdf"
    create_image_only_pdf(pdf_path)
    monkeypatch.setattr(
        "app.services.parsers.pdf_ocr.convert_from_path",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("poppler missing")),
    )

    result = PdfOcrCandidateParser().parse(ParserInput(parser_format="pdf_ocr_candidate", source_path=pdf_path))

    assert result.status == "failed"
    assert result.pdf_row_candidates == []
    assert result.warnings == ["OCR extraction failed with local tools: RuntimeError: poppler missing"]
