"""Create lightweight synthetic demo input files.

The generated files are safe to commit or share because they contain no real
medical or partner data. They are intended for local smoke tests and demos.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from openpyxl import Workbook


SERVICE_ROWS = [
    {
        "ID": "SVC-001",
        "specialty": "Diagnostics",
        "Специальность": "Diagnostics",
        "Code": "LAB-001",
        "Name_ru": "Complete blood count",
        "TarificatrCode": "T-1001",
    },
    {
        "ID": "SVC-002",
        "specialty": "Diagnostics",
        "Специальность": "Diagnostics",
        "Code": "IMG-010",
        "Name_ru": "Chest X-ray",
        "TarificatrCode": "T-2010",
    },
    {
        "ID": "SVC-003",
        "specialty": "Consultation",
        "Специальность": "Consultation",
        "Code": "CONS-100",
        "Name_ru": "General practitioner consultation",
        "TarificatrCode": "T-3100",
    },
]

PRICE_ROWS = [
    ("Service", "Resident price", "Nonresident price", "Code"),
    ("Diagnostics", None, None, None),
    ("Complete blood count", 2500, 3000, "LAB-001"),
    ("Chest X-ray", 7000, 8500, "IMG-010"),
    ("General practitioner consultation", 10000, 12000, "CONS-100"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic MedArchive demo files.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/samples"), help="Directory for generated files.")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    services_path = output_dir / "services.json"
    services_path.write_text(json.dumps({"services": SERVICE_ROWS}, ensure_ascii=False, indent=2), encoding="utf-8")

    workbook_path = output_dir / "demo_partner_prices.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "MedPartners Demo"
    sheet.append(["MedPartners Demo Clinic"])
    sheet.append(["Effective date", "2026-06-01"])
    sheet.append([])
    for row in PRICE_ROWS:
        sheet.append(row)
    workbook.save(workbook_path)

    archive_path = output_dir / "archive.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(workbook_path, arcname=workbook_path.name)

    print(f"Created {services_path}")
    print(f"Created {workbook_path}")
    print(f"Created {archive_path}")


if __name__ == "__main__":
    main()
