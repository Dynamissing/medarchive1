from __future__ import annotations

import json
from collections.abc import Iterator

import pytest
from openpyxl import Workbook
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Service, ServiceSynonym
from app.services.admin.service_directory_import import import_service_directory, normalize_text


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        yield session
    Base.metadata.drop_all(engine)


def test_import_json_is_idempotent_by_batch_and_source_hash(
    tmp_path,
    db_session: Session,
) -> None:
    source_path = tmp_path / "services.json"
    source_path.write_text(
        json.dumps(
            [
                {
                    "ID": "1",
                    "Специальность": "Кардиология",
                    "Code": "A-001",
                    "Name_ru": "Консультация кардиолога",
                    "TarificatrCode": "T-001",
                },
                {
                    "ID": "2",
                    "Специальность": "Кардиология",
                    "Code": "A-001",
                    "Name_ru": "Консультация кардиолога",
                    "TarificatrCode": "T-001",
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    first = import_service_directory(db_session, source_path, batch="unit-batch")
    second = import_service_directory(db_session, source_path, batch="unit-batch")

    services = db_session.scalars(select(Service)).all()
    synonyms = db_session.scalars(select(ServiceSynonym)).all()
    assert first.imported == 2
    assert second.imported == 0
    assert second.updated == 2
    assert len(services) == 2
    assert len(synonyms) >= 2
    assert services[0].code == "A-001"
    assert services[0].tariff_code == "T-001"
    assert services[0].category == "Кардиология"
    assert services[0].normalized_name == "консультация кардиолога"


def test_import_xlsx_logs_error_cells_and_skips_missing_name(
    tmp_path,
    db_session: Session,
) -> None:
    source_path = tmp_path / "services.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["ID", "Специальность", "Code", "Name_ru", "TarificatrCode"])
    worksheet.append(["10", "Диагностика", "#DIV/0!", "МРТ головного мозга", "MRI-001"])
    worksheet["C2"].data_type = "e"
    worksheet.append(["11", "Диагностика", "MRI-002", None, "MRI-002"])
    workbook.save(source_path)

    result = import_service_directory(db_session, source_path, batch="xlsx-batch")

    services = db_session.scalars(select(Service)).all()
    assert result.rows_seen == 2
    assert result.imported == 1
    assert result.skipped == 1
    assert len(result.warnings) == 2
    assert len(services) == 1
    assert services[0].code is None
    assert services[0].warnings
    assert services[0].name_ru == "МРТ головного мозга"


def test_duplicate_names_and_codes_do_not_crash_import(
    tmp_path,
    db_session: Session,
) -> None:
    source_path = tmp_path / "duplicates.json"
    source_path.write_text(
        json.dumps(
            [
                {"ID": "1", "Code": "DUP", "Name_ru": "Общий анализ крови"},
                {"ID": "2", "Code": "DUP", "Name_ru": "Общий анализ крови"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = import_service_directory(db_session, source_path, batch="duplicate-batch")

    services = db_session.scalars(select(Service)).all()
    assert result.imported == 2
    assert len(services) == 2
    assert {service.source_row_id for service in services} == {"1", "2"}


def test_normalize_text_is_deterministic() -> None:
    assert normalize_text("  МРТ: головного   мозга! ") == "мрт головного мозга"
