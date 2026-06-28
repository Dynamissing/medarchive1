from __future__ import annotations

from app.services.parsers.adapters import (
    DocxParser,
    PdfOcrCandidateParser,
    PdfTextParser,
    XlsParser,
    XlsxParser,
)
from app.services.parsers.base import DocumentParser


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, type[DocumentParser]] = {}

    def register(self, parser_class: type[DocumentParser]) -> None:
        self._parsers[parser_class.parser_format] = parser_class

    def resolve(self, parser_format: str | None) -> DocumentParser | None:
        if parser_format is None:
            return None
        parser_class = self._parsers.get(parser_format)
        if parser_class is None:
            return None
        return parser_class()


def build_default_parser_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(XlsxParser)
    registry.register(XlsParser)
    registry.register(DocxParser)
    registry.register(PdfTextParser)
    registry.register(PdfOcrCandidateParser)
    return registry


default_parser_registry = build_default_parser_registry()
