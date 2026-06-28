from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("ADMIN_USERNAME", "demo")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("ADMIN_TOKEN_SECRET", "test-secret")
    monkeypatch.setenv("ADMIN_TOKEN_TTL_SECONDS", "3600")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    get_settings.cache_clear()


def test_admin_login_returns_bearer_token_and_allows_admin_route(client: TestClient) -> None:
    login = client.post("/admin/login", json={"username": "demo", "password": "secret"})

    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["token_type"] == "bearer"

    response = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_admin_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/admin/dashboard")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_login_and_invalid_token_are_rejected(client: TestClient) -> None:
    bad_login = client.post("/admin/login", json={"username": "demo", "password": "wrong"})
    bad_token = client.get("/admin/dashboard", headers={"Authorization": "Bearer nope"})

    assert bad_login.status_code == 401
    assert bad_token.status_code == 401


def test_public_endpoints_remain_open(client: TestClient) -> None:
    health = client.get("/health")
    services = client.get("/services")

    assert health.status_code == 200
    assert services.status_code == 200


def test_openapi_exposes_bearer_auth_for_swagger(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/admin/dashboard"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "security" not in schema["paths"]["/services"]["get"]
