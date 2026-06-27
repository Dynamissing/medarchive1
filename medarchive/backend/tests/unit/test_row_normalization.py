from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.schemas.parsed_document import PdfRowCandidate, SpreadsheetPriceVariant, SpreadsheetRowCandidate
from app.services.normalization.row_normalization import (
    infer_partner_name,
    normalize_docx_table_row,
    normalize_pdf_candidate,
    normalize_service_name,
    normalize_source_code,
    normalize_spreadsheet_candidate,
    parse_currency,
    parse_effective_date,
    parse_price,
)


def test_price_currency_date_and_code_parsing() -> None:
    assert parse_price("1 234,50 тг") == Decimal("1234.50")
    assert parse_price("12\u00a0345.70 KZT") == Decimal("12345.70")
    assert parse_currency("стоимость", "1 000 тенге") == "KZT"
    assert parse_currency("price $ 30") == "USD"
    assert parse_effective_date("Клиника 5 прайс 2025.pdf") == date(2025, 1, 1)
    assert parse_effective_date("актуально с 05.03.2026") == date(2026, 3, 5)
    assert normalize_source_code(" A 01.02 ") == "A01.02"
    assert normalize_service_name("001 - Консультация терапевта: цена") == "Консультация терапевта"


def test_spreadsheet_candidate_normalizes_to_price_item_payload() -> None:
    candidate = SpreadsheetRowCandidate(
        sheet_name="Prices",
        row_index=12,
        category_path=["Diagnostics"],
        raw_values=["A-1", "МРТ головного мозга", "1 200", "1 000"],
        values={
            "code": " A-1 ",
            "service name": "МРТ головного мозга",
            "price cash": "1 200 тг",
            "price insurance": "1 000",
        },
        source_cells={"service name": "B12", "price cash": "C12", "price insurance": "D12"},
        price_variants=[
            SpreadsheetPriceVariant(label="price cash", value="1 200 тг", cell="C12"),
            SpreadsheetPriceVariant(label="price insurance", value="1 000", cell="D12"),
        ],
    )

    payload = normalize_spreadsheet_candidate(
        candidate,
        source_filename="Клиника 6 прайс 2026.xlsx",
        document_text="",
    )

    assert payload is not None
    assert payload.service_name == "МРТ головного мозга"
    assert payload.normalized_service_name == "МРТ головного мозга"
    assert payload.source_code == "A-1"
    assert payload.partner_name == "Клиника 6"
    assert payload.effective_date == date(2026, 1, 1)
    assert payload.category_path == ["Diagnostics"]
    assert payload.source_locator["sheet_name"] == "Prices"
    assert payload.source_locator["row_index"] == 12
    assert payload.amounts[0].amount == Decimal("1200.00")
    assert payload.amounts[0].currency == "KZT"
    assert payload.amounts[1].amount == Decimal("1000.00")


def test_category_rows_are_not_emitted() -> None:
    candidate = SpreadsheetRowCandidate(
        sheet_name="Prices",
        row_index=4,
        raw_values=["Diagnostics"],
        values={"service name": "Diagnostics"},
        source_cells={"service name": "A4"},
        price_variants=[],
    )

    assert normalize_spreadsheet_candidate(candidate) is None


def test_pdf_candidate_preserves_locator_and_low_confidence_warning() -> None:
    candidate = PdfRowCandidate(
        page_number=3,
        row_index=8,
        locator="page:3:row:8",
        text="001 Consultation therapist 500",
        raw_lines=["001 Consultation therapist 500"],
        values={"code": "001", "service_text": "Consultation therapist", "price": "500", "price_variants": ["500"]},
        confidence=0.42,
        low_confidence=True,
    )

    payload = normalize_pdf_candidate(candidate, source_filename="Clinic 1 2026.pdf")

    assert payload is not None
    assert payload.service_name == "Consultation therapist"
    assert payload.source_code == "001"
    assert payload.partner_name == "Clinic 1"
    assert payload.effective_date == date(2026, 1, 1)
    assert payload.source_locator == {"type": "pdf", "page_number": 3, "row_index": 8, "locator": "page:3:row:8"}
    assert payload.amounts[0].amount == Decimal("500.00")
    assert payload.warnings == ["Low-confidence OCR row."]


def test_docx_table_row_normalization() -> None:
    row = {"row_index": 2, "locator": "table:0:row:2", "values": ["A-10", "Blood test", "2 500 KZT"]}

    payload = normalize_docx_table_row(row, source_filename="Clinic 1 price 2024.docx")

    assert payload is not None
    assert payload.source_code == "A-10"
    assert payload.service_name == "Blood test"
    assert payload.amounts[0].amount == Decimal("2500.00")
    assert payload.amounts[0].currency == "KZT"
    assert payload.source_locator["locator"] == "table:0:row:2"


def test_partner_name_nullable_when_not_inferred() -> None:
    assert infer_partner_name("unknown.pdf", "plain content") is None
