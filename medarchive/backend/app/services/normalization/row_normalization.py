from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.parsed_document import PdfRowCandidate, SpreadsheetPriceVariant, SpreadsheetRowCandidate

SPACE_RE = re.compile(r"\s+")
CODE_PREFIX_RE = re.compile(r"^\s*((?:[A-Za-zА-Яа-я]\s*[-.]?\s*)?\d+(?:[.\-/]\d+)*)\b")
CODE_CELL_RE = re.compile(r"^\s*((?:[A-Za-zА-Яа-я]\s*[-.]?\s*)?\d+(?:[.\-/]\d+)*)\s*$")
YEAR_RE = re.compile(r"(20\d{2}|19\d{2})")
DATE_RE = re.compile(r"\b(\d{1,2})[.\-/](\d{1,2})[.\-/](20\d{2}|19\d{2})\b")
PRICE_RE = re.compile(r"(?<!\d)(?:\d{1,3}(?:[ \u00a0]\d{3})+|\d+)(?:[,.]\d{1,2})?(?!\d)")
CURRENCY_RE = re.compile(r"(KZT|₸|тг\.?|тенге|теңге|RUB|руб\.?|USD|\$|EUR|€)", re.IGNORECASE)
CATEGORY_HINTS = ("раздел", "категория", "итого", "всего", "примечание", "наименование услуг")
PRICE_HEADER_HINTS = ("цена", "стоимость", "price", "тариф", "сумма", "cash", "insurance")
NAME_HEADER_HINTS = ("service", "name", "наименование", "услуг", "услуга", "название")
CODE_HEADER_HINTS = ("code", "код", "шифр")


class PriceItemAmountPayload(BaseModel):
    label: str | None = None
    amount: Decimal
    currency: str | None = None
    raw_value: str


class PriceItemPayload(BaseModel):
    service_name: str
    normalized_service_name: str
    source_code: str | None = None
    partner_name: str | None = None
    effective_date: date | None = None
    category_path: list[str] = Field(default_factory=list)
    source_locator: dict[str, Any]
    raw_values: dict[str, Any] = Field(default_factory=dict)
    amounts: list[PriceItemAmountPayload] = Field(default_factory=list)
    is_category_row: bool = False
    warnings: list[str] = Field(default_factory=list)


def normalize_service_name(value: Any) -> str:
    text = normalize_text(str(value or ""))
    text = CODE_PREFIX_RE.sub("", text).strip(" -–—:;")
    text = re.sub(r"\b(price|цена|стоимость)\b\s*:?", "", text, flags=re.IGNORECASE)
    return normalize_text(text)


def normalize_source_code(value: Any) -> str | None:
    if value is None:
        return None
    text = normalize_text(str(value))
    match = CODE_PREFIX_RE.match(text)
    if not match:
        return None
    code = match.group(1)
    code = re.sub(r"\s+", "", code).upper().strip(" .:-")
    return code or None


def normalize_source_code_cell(value: Any) -> str | None:
    if value is None:
        return None
    match = CODE_CELL_RE.match(normalize_text(str(value)))
    if not match:
        return None
    code = re.sub(r"\s+", "", match.group(1)).upper().strip(" .:-")
    return code or None


def parse_price(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, int | float | Decimal):
        return Decimal(str(value)).quantize(Decimal("0.01"))
    text = str(value)
    match = PRICE_RE.search(text)
    if not match:
        return None
    number = match.group(0).replace("\u00a0", " ").replace(" ", "")
    if "," in number and "." not in number:
        number = number.replace(",", ".")
    try:
        return Decimal(number).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def parse_currency(*values: Any) -> str | None:
    joined = " ".join(str(value) for value in values if value is not None)
    match = CURRENCY_RE.search(joined)
    if not match:
        return None
    token = match.group(1).casefold().strip(".")
    if token in {"kzt", "₸", "тг", "тенге", "теңге"}:
        return "KZT"
    if token in {"rub", "руб"}:
        return "RUB"
    if token in {"usd", "$"}:
        return "USD"
    if token in {"eur", "€"}:
        return "EUR"
    return token.upper()


def parse_effective_date(*values: Any) -> date | None:
    joined = " ".join(str(value) for value in values if value is not None)
    date_match = DATE_RE.search(joined)
    if date_match:
        day, month, year = (int(part) for part in date_match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None
    year_match = YEAR_RE.search(joined)
    if year_match:
        return date(int(year_match.group(1)), 1, 1)
    return None


def infer_partner_name(filename: str | None = None, content: str | None = None) -> str | None:
    candidates = [Path(filename).stem if filename else "", content or ""]
    for candidate in candidates:
        text = normalize_text(candidate)
        if not text:
            continue
        match = re.search(r"(клиника\s*\d+|clinic\s*\d+)", text, flags=re.IGNORECASE)
        if match:
            return normalize_text(match.group(1)).title()
        first_line = text.splitlines()[0] if "\n" in text else text
        if len(first_line) <= 80 and any(word in first_line.casefold() for word in ("clinic", "клиника", "мц", "центр")):
            return first_line
    return None


def is_category_or_non_data_row(text: str, amount_count: int = 0) -> bool:
    normalized = normalize_text(text).casefold()
    if not normalized:
        return True
    if amount_count > 0:
        return False
    if any(hint in normalized for hint in CATEGORY_HINTS):
        return True
    return len(normalized.split()) <= 5 and not PRICE_RE.search(normalized)


def normalize_spreadsheet_candidate(
    candidate: SpreadsheetRowCandidate,
    source_filename: str | None = None,
    document_text: str | None = None,
) -> PriceItemPayload | None:
    raw_values = dict(candidate.values)
    service_name = choose_service_name(raw_values)
    amounts = amounts_from_spreadsheet_prices(candidate.price_variants)
    if not service_name:
        service_name = choose_service_name_from_raw(candidate.raw_values)
    cleaned_name = normalize_service_name(service_name)
    source_code = choose_code(raw_values)
    locator = {
        "type": "spreadsheet",
        "sheet_name": candidate.sheet_name,
        "row_index": candidate.row_index,
        "source_cells": candidate.source_cells,
    }
    is_category = is_category_or_non_data_row(cleaned_name or " ".join(map(str, candidate.raw_values)), len(amounts))
    if is_category:
        return None
    return PriceItemPayload(
        service_name=service_name or cleaned_name,
        normalized_service_name=cleaned_name,
        source_code=source_code,
        partner_name=infer_partner_name(source_filename, document_text),
        effective_date=parse_effective_date(source_filename, document_text),
        category_path=candidate.category_path,
        source_locator=locator,
        raw_values=raw_values,
        amounts=amounts,
        is_category_row=False,
        warnings=[] if amounts else ["No parseable price amount found."],
    )


def normalize_pdf_candidate(
    candidate: PdfRowCandidate,
    source_filename: str | None = None,
    document_text: str | None = None,
) -> PriceItemPayload | None:
    values = dict(candidate.values)
    service_name = values.get("service_text") or candidate.text
    amounts = []
    for raw_price in values.get("price_variants", []) or []:
        amount = parse_price(raw_price)
        if amount is not None:
            amounts.append(
                PriceItemAmountPayload(
                    label=None,
                    amount=amount,
                    currency=parse_currency(raw_price, candidate.text),
                    raw_value=str(raw_price),
                )
            )
    cleaned_name = normalize_service_name(service_name)
    is_category = is_category_or_non_data_row(cleaned_name or candidate.text, len(amounts))
    if is_category:
        return None
    warnings = []
    if candidate.low_confidence:
        warnings.append("Low-confidence OCR row.")
    if not amounts:
        warnings.append("No parseable price amount found.")
    return PriceItemPayload(
        service_name=str(service_name),
        normalized_service_name=cleaned_name,
        source_code=normalize_source_code(values.get("code")),
        partner_name=infer_partner_name(source_filename, document_text),
        effective_date=parse_effective_date(source_filename, document_text),
        source_locator={
            "type": "pdf",
            "page_number": candidate.page_number,
            "row_index": candidate.row_index,
            "locator": candidate.locator,
        },
        raw_values={"text": candidate.text, "values": values},
        amounts=amounts,
        warnings=warnings,
    )


def normalize_docx_table_row(
    row: dict[str, Any],
    source_filename: str | None = None,
    document_text: str | None = None,
) -> PriceItemPayload | None:
    values = [str(value).strip() for value in row.get("values", []) if str(value).strip()]
    if not values:
        return None
    joined = " ".join(values)
    source_code = next((code for value in values if (code := normalize_source_code_cell(value)) is not None), None)
    amounts: list[PriceItemAmountPayload] = []
    service_parts: list[str] = []
    for value in values:
        if normalize_source_code_cell(value) is not None:
            continue
        amount = parse_price(value)
        if amount is None:
            service_parts.append(value)
        else:
            amounts.append(
                PriceItemAmountPayload(
                    label=None,
                    amount=amount,
                    currency=parse_currency(value, joined),
                    raw_value=value,
                )
            )
    service_name = normalize_text(" ".join(service_parts))
    cleaned_name = normalize_service_name(service_name)
    if is_category_or_non_data_row(cleaned_name or joined, len(amounts)):
        return None
    return PriceItemPayload(
        service_name=service_name,
        normalized_service_name=cleaned_name,
        source_code=source_code,
        partner_name=infer_partner_name(source_filename, document_text),
        effective_date=parse_effective_date(source_filename, document_text),
        source_locator={"type": "docx", "locator": row.get("locator"), "row_index": row.get("row_index")},
        raw_values={"values": values},
        amounts=amounts,
        warnings=[] if amounts else ["No parseable price amount found."],
    )


def amounts_from_spreadsheet_prices(price_variants: list[SpreadsheetPriceVariant]) -> list[PriceItemAmountPayload]:
    amounts: list[PriceItemAmountPayload] = []
    for variant in price_variants:
        amount = parse_price(variant.value)
        if amount is None:
            continue
        amounts.append(
            PriceItemAmountPayload(
                label=variant.label,
                amount=amount,
                currency=parse_currency(variant.value, variant.label),
                raw_value=str(variant.value),
            )
        )
    return amounts


def choose_service_name(values: dict[str, Any]) -> str | None:
    for label, value in values.items():
        normalized_label = label.casefold()
        if any(hint in normalized_label for hint in NAME_HEADER_HINTS):
            return str(value)
    return None


def choose_service_name_from_raw(values: list[Any]) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and parse_price(text) is None:
            return text
    return None


def choose_code(values: dict[str, Any]) -> str | None:
    for label, value in values.items():
        normalized_label = label.casefold()
        if any(hint in normalized_label for hint in CODE_HEADER_HINTS):
            return normalize_source_code(value)
    return None


def normalize_text(value: str) -> str:
    return SPACE_RE.sub(" ", value.replace("\u00a0", " ")).strip(" \t\r\n-–—:;")
