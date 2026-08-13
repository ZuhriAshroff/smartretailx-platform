import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVICE_ROOT.parents[1]
for path in (str(SERVICE_ROOT), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import os

TEST_DB_PATH = SERVICE_ROOT / "tests" / "test_product_service.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from libs.common.security import create_access_token


@pytest.fixture(autouse=True)
def _reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _mock_event_publisher(monkeypatch):
    monkeypatch.setattr("app.events.publisher.publish", lambda *a, **k: None)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token():
    return create_access_token(user_id=1, email="admin@smartretailx.com", role="admin")


@pytest.fixture
def customer_token():
    return create_access_token(user_id=2, email="customer@smartretailx.com", role="customer")
