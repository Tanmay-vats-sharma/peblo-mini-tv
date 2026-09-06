from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import password_hash
from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestingSessionLocal() as db:
        for role in UserRole:
            db.add(
                User(
                    email=f"{role.value}@example.test",
                    password_hash=password_hash.hash("password"),
                    role=role,
                    is_active=True,
                )
            )
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def tokens(client: TestClient) -> dict[str, str]:
    result = {}
    for role in ("admin", "editor", "viewer"):
        response = client.post(
            "/auth/login",
            json={
                "email": f"{role}@example.test",
                "password": "password",
            },
        )
        assert response.status_code == 200
        result[role] = response.json()["access_token"]
    return result


@pytest.fixture()
def auth_headers(tokens: dict[str, str]):
    return {
        role: {"Authorization": f"Bearer {token}"}
        for role, token in tokens.items()
    }
