from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from app.schemas.parsed_document import ParsedDocumentResult


@dataclass(frozen=True)
class ParserInput:
    parser_format: str
    source_path: Path
    file_asset_id: UUID | None = None
    mime_type: str | None = None
    extension: str | None = None


class DocumentParser:
    parser_name: str
    parser_format: str

    def parse(self, parser_input: ParserInput) -> ParsedDocumentResult:
        return ParsedDocumentResult(
            parser_name=self.parser_name,
            parser_format=self.parser_format,  # type: ignore[arg-type]
            source_file_asset_id=parser_input.file_asset_id,
            source_path=str(parser_input.source_path),
            metadata={
                "mime_type": parser_input.mime_type,
                "extension": parser_input.extension,
            },
            warnings=["Placeholder parser selected; extraction is not implemented yet."],
        )
