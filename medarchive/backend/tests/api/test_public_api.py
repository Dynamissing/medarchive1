from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import PriceItemVersionStatus
from app.db.base import Base
from app.db.models import PriceItemVersion, Service, ServiceSynonym
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        seed_data(session)
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_services_list_supports_pagination_sorting_and_filtering(client: TestClient) -> None:
    response = client.get("/services", params={"page": 1, "page_size": 1, "sort": "name", "direction": "asc"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"] == {"page": 1, "page_size": 1, "total": 3, "pages": 3}
    assert payload["items"][0]["name"] == "Blood test"

    filtered = client.get("/services", params={"category": "Diagnostics"})
    assert filtered.status_code == 200
    assert [item["name"] for item in filtered.json()["items"]] == ["MRI brain"]


def test_services_search_includes_synonyms(client: TestClient) -> None:
    response = client.get("/services", params={"q": "cbc"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 1
    assert payload["items"][0]["name"] == "Blood test"


def test_partners_and_partner_services(client: TestClient) -> None:
    partners = client.get("/partners", params={"sort": "services", "direction": "desc"})

    assert partners.status_code == 200
    partner_payload = partners.json()
    assert partner_payload["meta"]["total"] == 2
    assert partner_payload["items"][0]["name"] == "Clinic 1"
    assert partner_payload["items"][0]["service_count"] == 2

    partner_id = partner_payload["items"][0]["id"]
    services = client.get(f"/partners/{partner_id}/services", params={"sort": "name"})
    assert services.status_code == 200
    service_names = [item["service"]["name"] for item in services.json()["items"]]
    assert service_names == ["Blood test", "MRI brain"]


def test_service_partners(client: TestClient, db_session: Session) -> None:
    service = db_session.query(Service).filter(Service.name_ru == "Blood test").one()

    response = client.get(f"/services/{service.id}/partners")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 1
    assert payload["items"][0]["name"] == "Clinic 1"


def test_search_across_services_and_partners(client: TestClient) -> None:
    response = client.get("/search", params={"q": "clinic"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 2
    assert {item["type"] for item in payload["items"]} == {"partner"}

    mixed = client.get("/search", params={"q": "blood"})
    assert mixed.status_code == 200
    assert any(item["type"] == "service" and item["label"] == "Blood test" for item in mixed.json()["items"])


def test_openapi_contains_public_response_schemas(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    assert "ServiceListResponse" in schemas
    assert "PartnerListResponse" in schemas
    assert "SearchResponse" in schemas
    assert "/services" in response.json()["paths"]
    assert "/search" in response.json()["paths"]


def seed_data(db: Session) -> None:
    blood = add_service(db, "Blood test", "blood test", code="A-10", category="Lab")
    mri = add_service(db, "MRI brain", "mri brain", code="M-1", category="Diagnostics")
    add_service(db, "Cardiologist consultation", "cardiologist consultation", code="C-1", category="Consultation")
    db.add(ServiceSynonym(service_id=blood.id, value="CBC", normalized_value="cbc", source="unit"))
    db.add(
        PriceItemVersion(
            row_hash="row-1",
            partner_name="Clinic 1",
            service_id=blood.id,
            service_name=blood.name_ru,
            normalized_service_name=blood.normalized_name,
            source_code=blood.code,
            effective_date=date(2026, 1, 1),
            amount=Decimal("1000.00"),
            currency="KZT",
            amount_kzt=Decimal("1000.00"),
            amount_label="cash",
            status=PriceItemVersionStatus.ACTIVE.value,
            is_active=True,
            source_locator={},
            raw_payload={},
        )
    )
    db.add(
        PriceItemVersion(
            row_hash="row-2",
            partner_name="Clinic 1",
            service_id=mri.id,
            service_name=mri.name_ru,
            normalized_service_name=mri.normalized_name,
            source_code=mri.code,
            effective_date=date(2026, 1, 1),
            amount=Decimal("5000.00"),
            currency="KZT",
            amount_kzt=Decimal("5000.00"),
            amount_label="cash",
            status=PriceItemVersionStatus.ACTIVE.value,
            is_active=True,
            source_locator={},
            raw_payload={},
        )
    )
    db.add(
        PriceItemVersion(
            row_hash="row-3",
            partner_name="Clinic 2",
            service_id=mri.id,
            service_name=mri.name_ru,
            normalized_service_name=mri.normalized_name,
            source_code=mri.code,
            effective_date=date(2026, 1, 1),
            amount=Decimal("5200.00"),
            currency="KZT",
            amount_kzt=Decimal("5200.00"),
            amount_label="cash",
            status=PriceItemVersionStatus.ACTIVE.value,
            is_active=True,
            source_locator={},
            raw_payload={},
        )
    )
    db.commit()


def add_service(db: Session, name: str, normalized_name: str, *, code: str, category: str) -> Service:
    service = Service(
        import_batch="api-test",
        source_type="test",
        source_hash=f"{name}:{code}",
        code=code,
        category=category,
        name_ru=name,
        normalized_name=normalized_name,
        warnings=[],
        raw_data={},
    )
    db.add(service)
    db.flush()
    return service
