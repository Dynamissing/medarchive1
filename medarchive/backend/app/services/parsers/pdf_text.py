from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import pdfplumber

from app.schemas.parsed_document import ParsedDocumentResult, PdfRowCandidate
from app.services.parsers.base import DocumentParser, ParserInput

PRICE_RE = re.compile(r"(?<!\d)(?:\d{1,3}(?:[ \u00a0]\d{3})+|\d+)(?:[,.]\d{1,2})?(?!\d)")
CODE_RE = re.compile(r"^\s*((?:[A-Za-zА-Яа-я]\s*)?\d+(?:[.\-/]\d+)*)\b")
SPACE_RE = re.compile(r"\s+")


class PdfTextParser(DocumentParser):
    parser_name = "pdf_text"
    parser_format = "pdf_text"

    def parse(self, parser_input: ParserInput) -> ParsedDocumentResult:
        extraction = extract_pdf_text(parser_input.source_path)
        return ParsedDocumentResult(
            parser_name=self.parser_name,
            parser_format="pdf_text",
            status="parsed",
            source_file_asset_id=parser_input.file_asset_id,
            source_path=str(parser_input.source_path),
            extracted_text="\n\n".join(page.raw_text for page in extraction.pages),
            metadata={
                "page_count": len(extraction.pages),
                "candidate_count": len(extraction.row_candidates),
                "confidence": extraction.confidence,
                "page_text": [
                    {"page_number": page.page_number, "text": page.raw_text}
                    for page in extraction.pages
                ],
                "mime_type": parser_input.mime_type,
                "extension": parser_input.extension,
            },
            warnings=extraction.warnings,
            pdf_row_candidates=extraction.row_candidates,
        )


@dataclass(frozen=True)
class PdfPageText:
    page_number: int
    raw_text: str
    lines: list[str]


@dataclass(frozen=True)
class PdfExtraction:
    pages: list[PdfPageText]
    row_candidates: list[PdfRowCandidate]
    confidence: float
    warnings: list[str]


def extract_pdf_text(path: Path) -> PdfExtraction:
    warnings: list[str] = []
    pages = extract_pages_with_pymupdf(path)
    if not any(page.raw_text.strip() for page in pages):
        warnings.append("PyMuPDF produced no text; pdfplumber fallback was used.")
        pages = extract_pages_with_pdfplumber(path)
    elif extraction_text_length(pages) < 50:
        fallback_pages = extract_pages_with_pdfplumber(path)
        if extraction_text_length(fallback_pages) > extraction_text_length(pages):
            warnings.append("pdfplumber fallback produced more text than PyMuPDF.")
            pages = fallback_pages

    row_candidates = build_pdf_row_candidates(pages)
    confidence = score_confidence(pages, row_candidates)
    if not row_candidates:
        warnings.append("No price-like row candidates were detected in text PDF.")
    return PdfExtraction(pages=pages, row_candidates=row_candidates, confidence=confidence, warnings=warnings)


def extract_pages_with_pymupdf(path: Path) -> list[PdfPageText]:
    pages: list[PdfPageText] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            raw_text = page.get_text("text")
            lines = lines_from_pymupdf_page(page)
            if not lines and raw_text:
                lines = normalize_lines(raw_text.splitlines())
            pages.append(PdfPageText(page_number=page_index, raw_text=raw_text, lines=lines))
    return pages


def lines_from_pymupdf_page(page) -> list[str]:
    text_dict = page.get_text("dict")
    positioned: list[tuple[float, float, str]] = []
    for block in text_dict.get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = normalize_text(" ".join(span.get("text", "") for span in spans))
            if not text:
                continue
            bbox = line.get("bbox", [0, 0, 0, 0])
            positioned.append((float(bbox[1]), float(bbox[0]), text))
    positioned.sort(key=lambda item: (round(item[0], 1), item[1]))
    return merge_positioned_lines(positioned)


def merge_positioned_lines(positioned: list[tuple[float, float, str]], y_tolerance: float = 2.5) -> list[str]:
    merged: list[str] = []
    current_y: float | None = None
    current_parts: list[tuple[float, str]] = []
    for y, x, text in positioned:
        if current_y is None or abs(y - current_y) <= y_tolerance:
            current_y = y if current_y is None else current_y
            current_parts.append((x, text))
            continue
        merged.append(" ".join(part for _x, part in sorted(current_parts)))
        current_y = y
        current_parts = [(x, text)]
    if current_parts:
        merged.append(" ".join(part for _x, part in sorted(current_parts)))
    return normalize_lines(merged)


def extract_pages_with_pdfplumber(path: Path) -> list[PdfPageText]:
    pages: list[PdfPageText] = []
    with pdfplumber.open(path) as document:
        for page_index, page in enumerate(document.pages, start=1):
            raw_text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
            pages.append(
                PdfPageText(
                    page_number=page_index,
                    raw_text=raw_text,
                    lines=normalize_lines(raw_text.splitlines()),
                )
            )
    return pages


def build_pdf_row_candidates(pages: list[PdfPageText]) -> list[PdfRowCandidate]:
    candidates: list[PdfRowCandidate] = []
    continuation_buffer: str | None = None
    for page in pages:
        assembled_lines = assemble_wrapped_lines(page.lines)
        for row_index, line in enumerate(assembled_lines, start=1):
            line_with_continuation = f"{continuation_buffer} {line}".strip() if continuation_buffer else line
            continuation_buffer = None
            if is_likely_continuation(line) and candidates:
                previous = candidates[-1]
                previous.text = normalize_text(f"{previous.text} {line}")
                previous.raw_lines.append(line)
                previous.values = infer_pdf_values(previous.text)
                previous.confidence = score_row_confidence(previous.text, previous.values)
                continue
            values = infer_pdf_values(line_with_continuation)
            if not values.get("price"):
                if looks_like_service_start(line):
                    continuation_buffer = line
                continue
            candidates.append(
                PdfRowCandidate(
                    page_number=page.page_number,
                    row_index=row_index,
                    locator=f"page:{page.page_number}:row:{row_index}",
                    text=line_with_continuation,
                    raw_lines=[line],
                    values=values,
                    confidence=score_row_confidence(line_with_continuation, values),
                )
            )
    return candidates


def assemble_wrapped_lines(lines: list[str]) -> list[str]:
    assembled: list[str] = []
    pending: str | None = None
    for line in lines:
        if not pending:
            pending = line
            continue
        if should_join_lines(pending, line):
            pending = normalize_text(f"{pending} {line}")
        else:
            assembled.append(pending)
            pending = line
    if pending:
        assembled.append(pending)
    return assembled


def should_join_lines(previous: str, current: str) -> bool:
    if has_price(previous):
        return False
    if has_price(current) and not CODE_RE.match(current):
        return True
    if is_likely_continuation(current):
        return True
    return False


def infer_pdf_values(text: str) -> dict[str, Any]:
    code_match = CODE_RE.match(text)
    code = normalize_text(code_match.group(1)) if code_match else None
    service_text = text
    if code:
        service_text = service_text[code_match.end() :].strip()
    prices = PRICE_RE.findall(service_text)
    if prices:
        service_text = service_text.rsplit(prices[-1], 1)[0].strip()
    return {
        "code": code,
        "service_text": normalize_text(service_text),
        "price": prices[-1] if prices else None,
        "price_variants": prices,
    }


def score_confidence(pages: list[PdfPageText], candidates: list[PdfRowCandidate]) -> float:
    if not pages:
        return 0.0
    text_score = min(extraction_text_length(pages) / 1000, 1.0) * 0.35
    row_score = min(len(candidates) / max(len(pages), 1) / 10, 1.0) * 0.45
    avg_row_score = (sum(candidate.confidence for candidate in candidates) / len(candidates) if candidates else 0) * 0.2
    return round(text_score + row_score + avg_row_score, 3)


def score_row_confidence(text: str, values: dict[str, Any]) -> float:
    score = 0.2
    if values.get("service_text"):
        score += 0.35
    if values.get("price"):
        score += 0.3
    if values.get("code"):
        score += 0.15
    if len(text) < 8:
        score -= 0.2
    return round(max(0.0, min(score, 1.0)), 3)


def has_price(text: str) -> bool:
    return bool(PRICE_RE.search(text))


def looks_like_service_start(text: str) -> bool:
    return bool(CODE_RE.match(text)) and len(text) > 8 and not text.endswith(":")


def is_likely_continuation(text: str) -> bool:
    return not CODE_RE.match(text) and not has_price(text) and len(text.split()) <= 8


def extraction_text_length(pages: list[PdfPageText]) -> int:
    return sum(len(page.raw_text.strip()) for page in pages)


def normalize_lines(lines: list[str]) -> list[str]:
    return [normalized for line in lines if (normalized := normalize_text(line))]


def normalize_text(text: str) -> str:
    return SPACE_RE.sub(" ", text.replace("\u00a0", " ")).strip()
