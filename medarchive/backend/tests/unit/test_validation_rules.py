from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.constants import AnomalySeverity, VerificationActionStatus
from app.db.base import Base
from app.db.models import AnomalyFlag, VerificationAction
from app.services.normalization.row_normalization import PriceItemAmountPayload, PriceItemPayload
from app.services.validation.price_history import PriceHistoryService
from app.services.validation.rules import LocalCurrencyConversionProvider, validate_document_rows, validate_price_row


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_validation_rules_flag_bad_row_values() -> None:
    row = row_payload(
        "",
        amounts=[
            PriceItemAmountPayload(label="resident", amount=Decimal("1000.00"), currency="KZT", raw_value="1000"),
            PriceItemAmountPayload(label="nonresident", amount=Decimal("900.00"), currency="KZT", raw_value="900"),
            PriceItemAmountPayload(label="foreign", amount=Decimal("-1.00"), currency="USD", raw_value="-1 USD"),
        ],
        effective_date=date.today() + timedelta(days=1),
    )

    issues = validate_price_row(
        row,
        conversion_provider=LocalCurrencyConversionProvider({"KZT": Decimal("1")}),
    )

    assert {issue.code for issue in issues} >= {
        "empty_service_name",
        "future_effective_date",
        "nonresident_less_than_resident",
        "non_positive_price",
        "non_kzt_preserved",
    }
    assert any(issue.severity == AnomalySeverity.ERROR for issue in issues)


def test_no_recognizable_data_document_error() -> None:
    issues = validate_document_rows([])

    assert len(issues) == 1
    assert issues[0].code == "no_recognizable_data_document"
    assert issues[0].severity == AnomalySeverity.ERROR


def test_flags_and_verification_actions_are_created_and_queryable(db_session: Session) -> None:
    row = row_payload(
        "Blood test",
        amounts=[PriceItemAmountPayload(label=None, amount=Decimal("0.00"), currency="KZT", raw_value="0")],
    )

    PriceHistoryService(db_session).validate_and_record(row)

    flags = db_session.scalars(select(AnomalyFlag)).all()
    actions = db_session.scalars(select(VerificationAction)).all()
    assert [flag.code for flag in flags] == ["non_positive_price"]
    assert flags[0].severity == AnomalySeverity.ERROR.value
    assert actions[0].anomaly_flag_id == flags[0].id
    assert actions[0].status == VerificationActionStatus.OPEN.value


def test_non_kzt_conversion_hook_can_convert_locally() -> None:
    row = row_payload(
        "Blood test",
        amounts=[PriceItemAmountPayload(label=None, amount=Decimal("10.00"), currency="USD", raw_value="10 USD")],
    )
    provider = LocalCurrencyConversionProvider({"USD": Decimal("500")})

    issues = validate_price_row(row, conversion_provider=provider)
    conversion = provider.convert_to_kzt(row.amounts[0].amount, row.amounts[0].currency)

    assert [issue.code for issue in issues] == []
    assert conversion.amount_kzt == Decimal("5000.00")


def row_payload(
    name: str,
    *,
    amounts: list[PriceItemAmountPayload] | None = None,
    effective_date: date | None = None,
) -> PriceItemPayload:
    return PriceItemPayload(
        service_name=name,
        normalized_service_name=name.casefold(),
        partner_name="Clinic 1",
        effective_date=effective_date or date(2026, 1, 1),
        source_locator={"type": "unit", "row_index": 1},
        raw_values={"name": name},
        amounts=amounts or [],
    )
