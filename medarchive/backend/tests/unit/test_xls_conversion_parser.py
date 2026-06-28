from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from app.services.parsers.base import ParserInput
from app.services.parsers.spreadsheet import XlsParser, find_libreoffice


def test_xls_parser_converts_to_xlsx_before_parsing(tmp_path: Path, monkeypatch) -> None:
    source_xls = tmp_path / "clinic.xls"
    source_xls.write_bytes(b"legacy-binary-placeholder")

    converted_dir = tmp_path / "converted"
    converted_dir.mkdir()
    converted_xlsx = converted_dir / "clinic.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Service", "Price"])
    sheet.append(["Ultrasound", 700])
    workbook.save(converted_xlsx)

    def fake_convert_xls_to_xlsx(source_path: Path) -> Path:
        assert source_path == source_xls
        return converted_xlsx

    monkeypatch.setattr(
        "app.services.parsers.spreadsheet.convert_xls_to_xlsx",
        fake_convert_xls_to_xlsx,
    )

    result = XlsParser().parse(ParserInput(parser_format="xls", source_path=source_xls))

    assert result.status == "parsed"
    assert result.parser_format == "xls"
    assert len(result.row_candidates) == 1
    assert result.row_candidates[0].values["service"] == "Ultrasound"
    assert result.row_candidates[0].price_variants[0].value == 700
    assert "XLS converted to XLSX with LibreOffice before parsing." in result.warnings


def test_find_libreoffice_uses_configured_executable(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "soffice"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")

    monkeypatch.setenv("LIBREOFFICE_EXECUTABLE", str(executable))

    assert find_libreoffice() == executable
