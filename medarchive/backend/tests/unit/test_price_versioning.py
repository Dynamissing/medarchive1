from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.constants import PriceItemVersionStatus
from app.db.base import Base
from app.db.models import AnomalyFlag, PriceItemVersion
from app.services.normalization.row_normalization import PriceItemAmountPayload, PriceItemPayload
from app.services.validation.price_history import PriceHistoryService
from app.services.validation.rules import LocalCurrencyConversionProvider


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_duplicate_same_partner_service_date_is_deterministic(db_session: Session) -> None:
    service = PriceHistoryService(db_session)
    row = row_payload("Blood test", Decimal("1000.00"))

    first = service.validate_and_record(row)[0]
    second = service.validate_and_record(row)[0]

    versions = db_session.scalars(select(PriceItemVersion)).all()
    flags = db_session.scalars(select(AnomalyFlag)).all()
    assert first.id == second.id
    assert len(versions) == 1
    assert versions[0].is_active is True
    assert [flag.code for flag in flags] == ["duplicate_same_partner_service_date"]


def test_new_price_supersedes_active_version_without_overwrite(db_session: Session) -> None:
    service = PriceHistoryService(db_session)
    old_row = row_payload("Blood test", Decimal("1000.00"))
    new_row = row_payload("Blood test", Decimal("1300.00"))

    old_version = service.validate_and_record(old_row)[0]
    new_version = service.validate_and_record(new_row)[0]
    db_session.refresh(old_version)
    db_session.refresh(new_version)

    versions = db_session.scalars(select(PriceItemVersion).order_by(PriceItemVersion.created_at)).all()
    assert len(versions) == 2
    assert old_version.amount == Decimal("1000.00")
    assert old_version.is_active is False
    assert old_version.status == PriceItemVersionStatus.INACTIVE.value
    assert old_version.superseded_by_id == new_version.id
    assert new_version.previous_version_id == old_version.id
    assert new_version.is_active is True


def test_price_change_gt_50_percent_creates_anomaly_flag(db_session: Session) -> None:
    service = PriceHistoryService(db_session)

    service.validate_and_record(row_payload("Blood test", Decimal("1000.00")))
    service.validate_and_record(row_payload("Blood test", Decimal("1600.00")))

    flags = db_session.scalars(select(AnomalyFlag)).all()
    assert [flag.code for flag in flags] == ["price_change_gt_50_percent"]
    assert flags[0].payload["old_amount"] == "1000.00"
    assert flags[0].payload["new_amount"] == "1600.00"


def test_non_kzt_amount_is_preserved_with_optional_kzt_conversion(db_session: Session) -> None:
    service = PriceHistoryService(
        db_session,
        conversion_provider=LocalCurrencyConversionProvider({"USD": Decimal("500")}),
    )
    row = row_payload("Blood test", Decimal("10.00"), currency="USD")

    version = service.validate_and_record(row)[0]

    assert version.currency == "USD"
    assert version.amount == Decimal("10.00")
    assert version.amount_kzt == Decimal("5000.00")


def test_no_recognizable_data_does_not_create_price_version(db_session: Session) -> None:
    service = PriceHistoryService(db_session)
    row = PriceItemPayload(
        service_name="",
        normalized_service_name="",
        partner_name="Clinic 1",
        effective_date=date(2026, 1, 1),
        source_locator={"type": "unit", "row_index": 1},
        raw_values={},
        amounts=[],
    )

    versions = service.validate_and_record(row)

    assert versions == []
    assert db_session.scalars(select(PriceItemVersion)).all() == []
    assert {flag.code for flag in db_session.scalars(select(AnomalyFlag)).all()} == {
        "empty_service_name",
        "no_recognizable_data",
    }


def row_payload(name: str, amount: Decimal, currency: str = "KZT") -> PriceItemPayload:
    return PriceItemPayload(
        service_name=name,
        normalized_service_name=name.casefold(),
        partner_name="Clinic 1",
        effective_date=date(2026, 1, 1),
        source_locator={"type": "unit", "row_index": 1},
        raw_values={"name": name},
        amounts=[
            PriceItemAmountPayload(
                label="cash",
                amount=amount,
                currency=currency,
                raw_value=str(amount),
            )
        ],
    )
