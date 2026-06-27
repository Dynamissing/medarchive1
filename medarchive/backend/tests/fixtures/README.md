# Test Fixture Strategy

Fixtures should stay synthetic, small, and reproducible.

- Prefer generating XLSX, DOCX, PDF, and scanned-PDF samples in temporary directories with `fixtures.generators`.
- Keep checked-in binary files out of the repository unless they are tiny golden samples with clear provenance.
- Use one or two rows per fixture unless a parser branch specifically needs more.
- Mock OCR and external tools in tests so CI does not require Poppler, Tesseract language packs, or LibreOffice.
- Do not place sensitive or real medical archive data in this directory.
