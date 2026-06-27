from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.constants import MatchDecisionStatus
from app.db.base import Base
from app.db.models import MatchingCandidate, Service, ServiceSynonym
from app.services.matching.engine import LayeredMatchingEngine, MatchThresholdPolicy
from app.services.normalization.row_normalization import PriceItemPayload


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)


def test_exact_normalized_name_match_auto_accepts(db_session: Session) -> None:
    service = add_service(db_session, name="Blood test", normalized_name="blood test", code="A-10")
    row = row_payload("Blood test")

    result = LayeredMatchingEngine(db_session).match_row(row, persist_review=True)

    assert result.decision_status == MatchDecisionStatus.AUTO_ACCEPT
    assert result.candidates[0].service_id == service.id
    assert result.candidates[0].score == 1.0
    assert result.candidates[0].strategy == "exact_name"
    assert db_session.scalars(select(MatchingCandidate)).all() == []


def test_synonym_match_returns_explanation(db_session: Session) -> None:
    service = add_service(db_session, name="Magnetic resonance imaging", normalized_name="magnetic resonance imaging")
    add_synonym(db_session, service, "MRI brain")
    row = row_payload("MRI brain")

    result = LayeredMatchingEngine(db_session).match_row(row)

    assert result.decision_status == MatchDecisionStatus.AUTO_ACCEPT
    assert result.candidates[0].service_id == service.id
    assert result.candidates[0].strategy == "synonym"
    assert "synonym" in result.candidates[0].explanation.methods


def test_fuzzy_and_token_match_needs_review_and_persists(db_session: Session) -> None:
    service = add_service(db_session, name="Cardiologist consultation", normalized_name="cardiologist consultation")
    row = row_payload("Cardiologist consultation followup")

    result = LayeredMatchingEngine(db_session).match_row(row)

    assert result.decision_status == MatchDecisionStatus.NEEDS_REVIEW
    assert result.candidates[0].service_id == service.id
    assert result.candidates[0].score < 0.94
    stored = db_session.scalars(select(MatchingCandidate)).all()
    assert len(stored) == 1
    assert stored[0].decision_status == MatchDecisionStatus.NEEDS_REVIEW.value
    assert stored[0].explanation["components"]["rapidfuzz"] > 0


def test_source_code_hint_can_lift_to_review_not_auto_accept(db_session: Session) -> None:
    service = add_service(db_session, name="Ultrasound abdomen", normalized_name="ultrasound abdomen", code="U-42")
    row = row_payload("Unclear abdomen procedure", source_code="U-42")

    result = LayeredMatchingEngine(db_session).match_row(row)

    assert result.decision_status == MatchDecisionStatus.NEEDS_REVIEW
    assert result.candidates[0].service_id == service.id
    assert "source_code_hint" in result.candidates[0].explanation.methods


def test_unmatched_row_persists_empty_review_record(db_session: Session) -> None:
    add_service(db_session, name="Blood test", normalized_name="blood test")
    row = row_payload("Completely unrelated service name")

    result = LayeredMatchingEngine(db_session).match_row(row)

    assert result.decision_status == MatchDecisionStatus.UNMATCHED
    stored = db_session.scalars(select(MatchingCandidate)).all()
    assert len(stored) == 1
    assert stored[0].service_id is None
    assert stored[0].decision_status == MatchDecisionStatus.UNMATCHED.value


def test_threshold_policy_is_configurable(db_session: Session) -> None:
    service = add_service(db_session, name="Cardiologist consultation", normalized_name="cardiologist consultation")
    row = row_payload("Cardiologist consultation followup")
    thresholds = MatchThresholdPolicy(auto_accept=0.80, needs_review=0.50)

    result = LayeredMatchingEngine(db_session, thresholds=thresholds).match_row(row, persist_review=False)

    assert result.decision_status == MatchDecisionStatus.AUTO_ACCEPT
    assert result.candidates[0].service_id == service.id


def add_service(
    db: Session,
    *,
    name: str,
    normalized_name: str,
    code: str | None = None,
    tariff_code: str | None = None,
) -> Service:
    service = Service(
        import_batch="unit",
        source_type="test",
        source_hash=f"{name}:{normalized_name}:{code}:{tariff_code}",
        code=code,
        tariff_code=tariff_code,
        name_ru=name,
        normalized_name=normalized_name,
        warnings=[],
        raw_data={},
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def add_synonym(db: Session, service: Service, value: str) -> ServiceSynonym:
    synonym = ServiceSynonym(
        service_id=service.id,
        value=value,
        normalized_value=value.casefold(),
        source="unit",
    )
    db.add(synonym)
    db.commit()
    return synonym


def row_payload(name: str, source_code: str | None = None) -> PriceItemPayload:
    return PriceItemPayload(
        service_name=name,
        normalized_service_name=name.casefold(),
        source_code=source_code,
        source_locator={"type": "unit", "row_index": 1},
        raw_values={"name": name},
    )
