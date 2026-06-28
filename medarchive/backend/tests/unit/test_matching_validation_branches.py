from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.constants import MatchDecisionStatus
from app.db.base import Base
from app.db.models import AnomalyFlag, MatchingCandidate, Service, VerificationAction
from app.services.matching.engine import LayeredMatchingEngine
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


def test_matching_unmatched_branch_persists_review_record(db_session: Session) -> None:
    add_service(db_session, "Blood test", "blood test")
    row = row_payload("Completely unrelated procedure")

    result = LayeredMatchingEngine(db_session).match_row(row)

    stored = db_session.scalars(select(MatchingCandidate)).all()
    assert result.decision_status == MatchDecisionStatus.UNMATCHED
    assert len(stored) == 1
    assert stored[0].service_id is None
    assert stored[0].normalized_query == "completely unrelated procedure"


def test_validation_document_level_and_currency_fixture_branches(db_session: Session) -> None:
    service = PriceHistoryService(
        db_session,
        conversion_provider=LocalCurrencyConversionProvider({"EUR": Decimal("550")}),
    )
    service.persist_document_issue([], payload={"document": "empty.pdf"})
    row = row_payload(
        "Foreign currency service",
        amount=PriceItemAmountPayload(label="cash", amount=Decimal("2.00"), currency="EUR", raw_value="2 EUR"),
    )

    version = service.validate_and_record(row)[0]

    flags = db_session.scalars(select(AnomalyFlag)).all()
    actions = db_session.scalars(select(VerificationAction)).all()
    assert [flag.code for flag in flags] == ["no_recognizable_data_document"]
    assert actions[0].action_type == "review_document_extraction"
    assert version.currency == "EUR"
    assert version.amount_kzt == Decimal("1100.00")


def add_service(db: Session, name: str, normalized_name: str) -> Service:
    service = Service(
        import_batch="branch-test",
        source_type="test",
        source_hash=name,
        name_ru=name,
        normalized_name=normalized_name,
        warnings=[],
        raw_data={},
    )
    db.add(service)
    db.commit()
    return service


def row_payload(
    name: str,
    amount: PriceItemAmountPayload | None = None,
) -> PriceItemPayload:
    return PriceItemPayload(
        service_name=name,
        normalized_service_name=name.casefold(),
        partner_name="Clinic Branch",
        effective_date=date(2026, 1, 1),
        source_locator={"type": "unit"},
        raw_values={"name": name},
        amounts=[amount] if amount else [],
    )
