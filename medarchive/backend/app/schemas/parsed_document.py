from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

ParserFormat = Literal["xlsx", "xls", "docx", "pdf_text", "pdf_ocr_candidate"]
ParsedDocumentStatus = Literal["placeholder", "parsed", "failed"]


class SpreadsheetPriceVariant(BaseModel):
    label: str
    value: Any
    cell: str | None = None


class SpreadsheetRowCandidate(BaseModel):
    sheet_name: str
    row_index: int
    category_path: list[str] = Field(default_factory=list)
    raw_values: list[Any] = Field(default_factory=list)
    values: dict[str, Any] = Field(default_factory=dict)
    source_cells: dict[str, str] = Field(default_factory=dict)
    price_variants: list[SpreadsheetPriceVariant] = Field(default_factory=list)


class PdfRowCandidate(BaseModel):
    page_number: int
    row_index: int
    locator: str
    text: str
    raw_lines: list[str] = Field(default_factory=list)
    values: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    low_confidence: bool = False


class ParsedDocumentResult(BaseModel):
    parser_name: str
    parser_format: ParserFormat
    status: ParsedDocumentStatus = "placeholder"
    source_file_asset_id: UUID | None = None
    source_path: str | None = None
    extracted_text: str | None = None
    tables: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    row_candidates: list[SpreadsheetRowCandidate] = Field(default_factory=list)
    pdf_row_candidates: list[PdfRowCandidate] = Field(default_factory=list)
