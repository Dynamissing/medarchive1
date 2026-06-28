"""Import service directory rows into PostgreSQL."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.services.admin.service_directory_import import import_service_directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Import MedArchive service directory XLSX or JSON.")
    parser.add_argument("source_path", type=Path, help="Path to .xlsx or .json service directory.")
    parser.add_argument("--batch", help="Optional idempotency batch key.")
    args = parser.parse_args()

    configure_logging()
    with SessionLocal() as db:
        result = import_service_directory(db, args.source_path, batch=args.batch)

    print(
        "Imported service directory "
        f"batch={result.batch} rows_seen={result.rows_seen} "
        f"created={result.imported} updated={result.updated} "
        f"skipped={result.skipped} warnings={len(result.warnings)}"
    )


if __name__ == "__main__":
    main()
