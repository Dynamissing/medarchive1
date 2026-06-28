# Parsing Strategy

## Goal

Define how archive files will eventually be converted into structured metadata and reviewable records.

## Bootstrap Notes

- Service directory parsing is implemented for XLSX and JSON.
- Archive ZIP ingestion registers files and immediately enqueues parser processing.
- Parser selection is implemented for registered file types.
- XLSX extraction and XLS conversion-to-XLSX parsing are implemented.
- DOCX extraction is implemented.
- Text-PDF extraction is implemented.
- OCR-assisted PDF extraction is implemented for OCR-candidate PDFs when local OCR tools are installed.
- Extracted row normalization is implemented as deterministic parse-ready payload construction.
- Only synthetic or approved sample files should be used during development.
- Parser outputs should be typed and validated before being stored or matched.
- Backend parser tests use lightweight synthetic XLSX, DOCX, text-PDF, and scanned-PDF fixtures generated in temporary directories.

## Service Directory Import

- Supported formats: `.xlsx` and `.json`.
- Organizer XLSX columns currently handled: `ID`, `Специальность`, `Code`, `Name_ru`, and `TarificatrCode`.
- Spreadsheet error cells are converted to warnings and do not stop the import.
- Rows without a service name are skipped with a warning.
- Services are stored with source row id, tariff code, category/specialty, raw row data, warnings, and normalized text fields.
- Import idempotency is based on import batch plus deterministic source row hash.

## Archive ZIP Ingestion

- ZIP uploads are accepted through `POST /admin/import/archive`.
- ZIP imports can also run from a local path through `scripts/import_archive.py`.
- The original ZIP and extracted member files are preserved under the configured local storage root.
- File assets record SHA-256 hashes, size, extension, MIME guess, and storage path.
- Each extracted member creates a pending `price_documents` row and the import batch is queued for asynchronous parsing.
- If the Celery broker is unavailable during local development, the API process falls back to an in-process background parser task.

## Parser Abstraction

- Parser registry formats: `xlsx`, `xls`, `docx`, `pdf_text`, and `pdf_ocr_candidate`.
- Parser classes share a common `parse(ParserInput) -> ParsedDocumentResult` interface.
- PDF selection uses simple local byte heuristics: files with common text markers route to `pdf_text`; otherwise they route to `pdf_ocr_candidate`.
- The document processing service chooses parsers from stored file metadata and local file paths.
- XLSX and XLS parsers produce spreadsheet row candidates.
- DOCX parser extracts paragraphs, tables, raw text, and table row locators.
- Text-PDF parser extracts raw page text and page-located row candidates.
- PDF OCR-candidate parser uses local pdf2image and Tesseract OCR.

## Spreadsheet Extraction

- XLSX parsing supports multiple sheets, delayed header rows, two-row headers, merged header cells, category rows, empty rows, multiple price columns, and source coordinates.
- XLS parsing requires LibreOffice. The Docker backend image installs LibreOffice Calc, and local runs can set `LIBREOFFICE_EXECUTABLE` when `soffice` is not on `PATH`. The `.xls` file is converted to `.xlsx` in a temporary directory before using the same spreadsheet extraction logic.
- Category rows update row candidate context and are not emitted as price items.
- Row candidates preserve all detected price variants rather than flattening to one price.
- Each row candidate stores `sheet_name`, `row_index`, `category_path`, `raw_values`, normalized header-value pairs, `source_cells`, and `price_variants`.

## DOCX Extraction

- DOCX parsing uses `python-docx` for paragraph and table extraction.
- Raw text is preserved by joining paragraph text and table row text.
- Table rows include source locators formatted as `table:{table_index}:row:{row_index}`.
- Tracked-change detection scans DOCX OOXML for common WordprocessingML change tags such as `w:ins`, `w:del`, and property-change markers.
- If tracked changes are present or extraction quality is poor, a LibreOffice DOCX fallback conversion is attempted when LibreOffice is installed.
- Fallback failure is recorded as a warning; extraction still returns the direct `python-docx` result when available.

## Text PDF Extraction

- Text-PDF parsing uses PyMuPDF as the primary extractor.
- pdfplumber is used as a fallback when PyMuPDF produces no text or materially less text.
- Raw text is preserved per page in `metadata.page_text` and as joined `extracted_text`.
- Page row candidates include locators formatted as `page:{page_number}:row:{row_index}`.
- Block-based line grouping uses PyMuPDF spans and y-coordinate merging.
- Fragmented lines and line-wrapped service names are assembled before candidate detection.
- Multi-page continuation is handled for code-led service rows whose price appears on the next page.
- Extraction confidence is scored from available text volume, row density, and row-level signals.
- OCR is not run in this phase.

## OCR PDF Extraction

- OCR-candidate PDFs are detected with local heuristics based on low text availability and image-heavy pages.
- OCR conversion uses `pdf2image`, which requires local Poppler tools such as `pdfinfo` and `pdftoppm`.
- Image preprocessing uses grayscale conversion, autocontrast, median filtering, and thresholding before OCR.
- Tesseract is invoked locally with `rus+kaz+eng`.
- OCR artifacts are preserved per page in `metadata.page_text`, including raw OCR text, average confidence, languages, preprocessing steps, and line-level confidences.
- OCR row candidates reuse the PDF row assembly path and include page locators.
- Low-confidence rows are marked with `low_confidence: true`.
- If local OCR dependencies are missing, the parser returns a typed failed result with a warning instead of crashing.

## Row Normalization

- Spreadsheet, DOCX table, and PDF row candidates can be converted into `PriceItemPayload` and `PriceItemAmountPayload` structures.
- Normalization handles service name cleaning, source code normalization, category/non-data row detection, price parsing, currency parsing, effective date parsing, and partner name inference.
- Source locators are preserved from parser output, including sheet/row/cell metadata, DOCX table row locators, and PDF page row locators.
- Price variants are preserved as separate amount payloads when available.
- Partner names and effective dates remain nullable when they cannot be inferred deterministically.
- Normalization does not perform service matching, anomaly detection, versioning, or database persistence in this phase.

## ParsedDocumentResult

Stable placeholder result shape:

```json
{
  "parser_name": "xlsx_placeholder",
  "parser_format": "xlsx",
  "status": "placeholder",
  "source_file_asset_id": null,
  "source_path": "path/to/file.xlsx",
  "extracted_text": null,
  "tables": [],
  "metadata": {},
  "warnings": ["Placeholder parser selected; extraction is not implemented yet."],
  "row_candidates": []
}
```

## Open Questions

- Which document/archive source formats are required for the demo?
- Which metadata fields are mandatory?
- How should low-confidence extraction results be reviewed?
- What audit trail is required for medical archive handling?
