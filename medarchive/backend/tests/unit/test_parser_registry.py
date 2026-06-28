from __future__ import annotations

from pathlib import Path

from app.db.models import FileAsset
from app.schemas.parsed_document import ParsedDocumentResult
from app.services.document_processing import DocumentProcessingService
from app.services.parsers.adapters import (
    DocxParser,
    PdfOcrCandidateParser,
    PdfTextParser,
    XlsParser,
    XlsxParser,
)
from app.services.parsers.base import DocumentParser, ParserInput
from app.services.parsers.registry import default_parser_registry
from app.utils.file_detection import detect_file_type


def test_registry_resolves_spreadsheet_and_docx_formats(tmp_path: Path) -> None:
    samples = [
        ("Хакатон/Клиника 6 прайс 2026.xlsx", XlsxParser),
        ("Хакатон/Клиника 7_Прайс 2026.xls", XlsParser),
        ("Хакатон/Клиника 1 прайс 2024.docx", DocxParser),
    ]

    for filename, expected_parser_class in samples:
        sample_path = tmp_path / Path(filename).name
        sample_path.write_bytes(b"placeholder")
        detection = detect_file_type(filename=filename, path=sample_path)
        parser = default_parser_registry.resolve(detection.parser_format)
        assert isinstance(parser, expected_parser_class)


def test_registry_resolves_pdf_text_and_ocr_candidate(tmp_path: Path) -> None:
    text_pdf = tmp_path / "Клиника 1 2026.pdf"
    text_pdf.write_bytes(b"%PDF-1.7\n1 0 obj\n/Font <<>>\nBT (hello) Tj ET\n")
    scanned_pdf = tmp_path / "Клиника 3 прайс 2026.PDF"
    scanned_pdf.write_bytes(b"%PDF-1.7\n/image-only-placeholder\n")

    text_detection = detect_file_type(filename=text_pdf.name, path=text_pdf)
    scanned_detection = detect_file_type(filename=scanned_pdf.name, path=scanned_pdf)

    assert text_detection.parser_format == "pdf_text"
    assert isinstance(default_parser_registry.resolve(text_detection.parser_format), PdfTextParser)
    assert scanned_detection.parser_format == "pdf_ocr_candidate"
    assert isinstance(default_parser_registry.resolve(scanned_detection.parser_format), PdfOcrCandidateParser)


def test_document_processing_service_chooses_parser_from_file_asset_metadata(tmp_path: Path) -> None:
    source_path = tmp_path / "price.xlsx"
    source_path.write_bytes(b"placeholder")
    file_asset = FileAsset(
        import_batch_id="00000000-0000-0000-0000-000000000000",
        original_filename="price.xlsx",
        stored_path=str(source_path),
        sha256="abc",
        size_bytes=source_path.stat().st_size,
        extension=".xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        warnings=[],
    )

    parser = DocumentProcessingService().choose_parser(file_asset)

    assert isinstance(parser, XlsxParser)


def test_placeholder_parser_returns_typed_result(tmp_path: Path) -> None:
    class DummyPlaceholderParser(DocumentParser):
        parser_name = "dummy_placeholder"
        parser_format = "pdf_ocr_candidate"

    source_path = tmp_path / "price.pdf"
    source_path.write_bytes(b"placeholder")
    parser = DummyPlaceholderParser()

    result = parser.parse(
        ParserInput(
            parser_format="pdf_ocr_candidate",
            source_path=source_path,
            extension=".pdf",
            mime_type="application/pdf",
        )
    )

    assert isinstance(result, ParsedDocumentResult)
    assert result.parser_format == "pdf_ocr_candidate"
    assert result.status == "placeholder"
    assert result.extracted_text is None
    assert result.tables == []
    assert result.warnings == ["Placeholder parser selected; extraction is not implemented yet."]
