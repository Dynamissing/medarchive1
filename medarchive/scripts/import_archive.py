"""Import a ZIP archive into local storage and database rows."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.admin.archive_import import import_archive_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Import MedArchive ZIP archive from a local path.")
    parser.add_argument("source_path", type=Path, help="Path to a ZIP archive.")
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    with SessionLocal() as db:
        result = import_archive_path(db, args.source_path, settings.file_storage_root)

    print(
        "Imported archive "
        f"batch={result.import_batch_id} original_asset={result.original_asset_id} "
        f"extracted_files={result.extracted_files} "
        f"price_documents={result.price_documents} warnings={len(result.warnings)}"
    )


if __name__ == "__main__":
    main()
