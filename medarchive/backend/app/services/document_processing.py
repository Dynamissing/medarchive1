from __future__ import annotations

from pathlib import Path

from app.db.models import FileAsset, PriceDocument
from app.schemas.parsed_document import ParsedDocumentResult
from app.services.parsers import ParserInput, ParserRegistry, default_parser_registry
from app.utils.file_detection import detect_file_type


class UnsupportedDocumentFormatError(ValueError):
    pass


class DocumentProcessingService:
    def __init__(self, parser_registry: ParserRegistry | None = None) -> None:
        self.parser_registry = parser_registry or default_parser_registry

    def choose_parser(self, file_asset: FileAsset):
        detection = detect_file_type(
            filename=file_asset.original_filename,
            mime_type=file_asset.mime_type,
            path=Path(file_asset.stored_path),
        )
        return self.parser_registry.resolve(detection.parser_format)

    def parse_price_document(self, price_document: PriceDocument) -> ParsedDocumentResult:
        file_asset = price_document.file_asset
        source_path = Path(file_asset.stored_path)
        detection = detect_file_type(
            filename=file_asset.original_filename,
            mime_type=file_asset.mime_type,
            path=source_path,
        )
        parser = self.parser_registry.resolve(detection.parser_format)
        if parser is None:
            raise UnsupportedDocumentFormatError(
                f"No parser registered for file {file_asset.original_filename!r}"
            )
        return parser.parse(
            ParserInput(
                parser_format=detection.parser_format or "",
                source_path=source_path,
                file_asset_id=file_asset.id,
                mime_type=detection.mime_type,
                extension=detection.extension,
            )
        )
