from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageOps
from pytesseract import Output

from app.schemas.parsed_document import ParsedDocumentResult, PdfRowCandidate
from app.services.parsers.base import DocumentParser, ParserInput
from app.services.parsers.pdf_text import (
    build_pdf_row_candidates,
    extraction_text_length,
    normalize_lines,
    score_confidence,
)

OCR_LANGUAGES = "rus+kaz+eng"
LOW_CONFIDENCE_THRESHOLD = 0.55


class PdfOcrCandidateParser(DocumentParser):
    parser_name = "pdf_ocr_candidate"
    parser_format = "pdf_ocr_candidate"

    def parse(self, parser_input: ParserInput) -> ParsedDocumentResult:
        try:
            extraction = extract_pdf_with_ocr(parser_input.source_path)
        except Exception as exc:
            return ParsedDocumentResult(
                parser_name=self.parser_name,
                parser_format="pdf_ocr_candidate",
                status="failed",
                source_file_asset_id=parser_input.file_asset_id,
                source_path=str(parser_input.source_path),
                metadata={
                    "ocr_candidate": is_ocr_candidate_pdf(parser_input.source_path),
                    "ocr_languages": OCR_LANGUAGES,
                    "mime_type": parser_input.mime_type,
                    "extension": parser_input.extension,
                },
                warnings=[f"OCR extraction failed with local tools: {type(exc).__name__}: {exc}"],
            )
        return ParsedDocumentResult(
            parser_name=self.parser_name,
            parser_format="pdf_ocr_candidate",
            status="parsed",
            source_file_asset_id=parser_input.file_asset_id,
            source_path=str(parser_input.source_path),
            extracted_text="\n\n".join(page.raw_text for page in extraction.pages),
            metadata={
                "page_count": len(extraction.pages),
                "candidate_count": len(extraction.row_candidates),
                "confidence": extraction.confidence,
                "ocr_candidate": extraction.ocr_candidate,
                "ocr_languages": OCR_LANGUAGES,
                "page_text": [
                    {
                        "page_number": page.page_number,
                        "text": page.raw_text,
                        "ocr_confidence": page.ocr_confidence,
                        "artifact": page.artifact,
                    }
                    for page in extraction.pages
                ],
                "mime_type": parser_input.mime_type,
                "extension": parser_input.extension,
            },
            warnings=extraction.warnings,
            pdf_row_candidates=extraction.row_candidates,
        )


@dataclass(frozen=True)
class OcrPageText:
    page_number: int
    raw_text: str
    lines: list[str]
    line_confidences: list[float | None]
    ocr_confidence: float | None
    artifact: dict[str, Any]


@dataclass(frozen=True)
class OcrExtraction:
    pages: list[OcrPageText]
    row_candidates: list[PdfRowCandidate]
    confidence: float
    ocr_candidate: bool
    warnings: list[str]


def extract_pdf_with_ocr(path: Path) -> OcrExtraction:
    warnings: list[str] = []
    ocr_candidate = is_ocr_candidate_pdf(path)
    pages = ocr_pages(path)
    candidate_pages = [
        _page_to_pdf_text(page)
        for page in pages
    ]
    row_candidates = build_pdf_row_candidates(candidate_pages)
    for candidate in row_candidates:
        page = pages[candidate.page_number - 1]
        line_confidence = confidence_for_candidate(candidate.raw_lines, page)
        confidence_source = line_confidence if line_confidence is not None else page.ocr_confidence
        combined_confidence = min(candidate.confidence, confidence_source if confidence_source is not None else candidate.confidence)
        candidate.confidence = round(combined_confidence, 3)
        candidate.low_confidence = candidate.confidence < LOW_CONFIDENCE_THRESHOLD

    confidence = score_confidence(candidate_pages, row_candidates)
    if pages:
        page_confidences = [page.ocr_confidence for page in pages if page.ocr_confidence is not None]
        if page_confidences:
            confidence = round(min(confidence, sum(page_confidences) / len(page_confidences)), 3)
    if not row_candidates:
        warnings.append("No price-like row candidates were detected from OCR text.")
    if any(candidate.low_confidence for candidate in row_candidates):
        warnings.append("One or more OCR row candidates were marked low confidence.")

    return OcrExtraction(
        pages=pages,
        row_candidates=row_candidates,
        confidence=confidence,
        ocr_candidate=ocr_candidate,
        warnings=warnings,
    )


def is_ocr_candidate_pdf(path: Path, min_text_chars_per_page: int = 25) -> bool:
    try:
        with fitz.open(path) as document:
            if len(document) == 0:
                return True
            text_chars = sum(len(page.get_text("text").strip()) for page in document)
            image_blocks = 0
            for page in document:
                for block in page.get_text("dict").get("blocks", []):
                    if block.get("type") == 1:
                        image_blocks += 1
            low_text = text_chars / max(len(document), 1) < min_text_chars_per_page
            return low_text or (image_blocks > 0 and text_chars < 200)
    except Exception:
        return True


def ocr_pages(path: Path) -> list[OcrPageText]:
    images = convert_from_path(path, dpi=300)
    pages: list[OcrPageText] = []
    for page_index, image in enumerate(images, start=1):
        processed = preprocess_image(image)
        ocr_data = pytesseract.image_to_data(
            processed,
            lang=OCR_LANGUAGES,
            output_type=Output.DICT,
            config="--psm 6",
        )
        text, line_confidences, confidence = text_from_ocr_data(ocr_data)
        lines = normalize_lines(text.splitlines())
        pages.append(
            OcrPageText(
                page_number=page_index,
                raw_text=text,
                lines=lines,
                line_confidences=line_confidences,
                ocr_confidence=confidence,
                artifact={
                    "engine": "tesseract",
                    "languages": OCR_LANGUAGES,
                    "preprocessing": ["grayscale", "autocontrast", "median_filter", "threshold"],
                    "word_count": len([word for word in ocr_data.get("text", []) if str(word).strip()]),
                    "line_confidences": line_confidences,
                },
            )
        )
    return pages


def preprocess_image(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    enhanced = ImageOps.autocontrast(grayscale)
    denoised = enhanced.filter(ImageFilter.MedianFilter(size=3))
    return denoised.point(lambda pixel: 255 if pixel > 180 else 0)


def text_from_ocr_data(ocr_data: dict[str, list[Any]]) -> tuple[str, list[float | None], float | None]:
    grouped: dict[tuple[int, int, int], list[tuple[int, str]]] = {}
    grouped_confidences: dict[tuple[int, int, int], list[float]] = {}
    confidences: list[float] = []
    texts = ocr_data.get("text", [])
    confs = ocr_data.get("conf", [])
    lefts = ocr_data.get("left", [])
    block_nums = ocr_data.get("block_num", [])
    par_nums = ocr_data.get("par_num", [])
    line_nums = ocr_data.get("line_num", [])

    for index, raw_text in enumerate(texts):
        text = str(raw_text).strip()
        if not text:
            continue
        try:
            confidence = float(confs[index])
        except (ValueError, TypeError, IndexError):
            confidence = -1.0
        if confidence >= 0:
            normalized_confidence = confidence / 100
            confidences.append(normalized_confidence)
        else:
            normalized_confidence = None
        key = (
            int(block_nums[index]) if index < len(block_nums) else 0,
            int(par_nums[index]) if index < len(par_nums) else 0,
            int(line_nums[index]) if index < len(line_nums) else index,
        )
        left = int(lefts[index]) if index < len(lefts) else index
        grouped.setdefault(key, []).append((left, text))
        if normalized_confidence is not None:
            grouped_confidences.setdefault(key, []).append(normalized_confidence)

    lines: list[str] = []
    line_confidences: list[float | None] = []
    for key, words in sorted(grouped.items()):
        lines.append(" ".join(word for _left, word in sorted(words)))
        line_values = grouped_confidences.get(key, [])
        line_confidences.append(round(sum(line_values) / len(line_values), 3) if line_values else None)
    avg_confidence = round(sum(confidences) / len(confidences), 3) if confidences else None
    return "\n".join(lines), line_confidences, avg_confidence


def confidence_for_candidate(raw_lines: list[str], page: OcrPageText) -> float | None:
    confidence_values: list[float] = []
    for raw_line in raw_lines:
        try:
            line_index = page.lines.index(raw_line)
        except ValueError:
            continue
        if line_index < len(page.line_confidences):
            confidence = page.line_confidences[line_index]
            if confidence is not None:
                confidence_values.append(confidence)
    if not confidence_values:
        return None
    return round(sum(confidence_values) / len(confidence_values), 3)


def _page_to_pdf_text(page: OcrPageText):
    from app.services.parsers.pdf_text import PdfPageText

    return PdfPageText(page_number=page.page_number, raw_text=page.raw_text, lines=page.lines)
