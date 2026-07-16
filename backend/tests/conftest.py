import hashlib
import hmac
import os
import time

from cryptography.fernet import Fernet

os.environ["SIGNALFLOW_DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["INTEGRATION_MODE"] = "mock"
os.environ["SIGNALFLOW_MOCK_EXTERNAL_SERVICES"] = "true"
os.environ["OWNER_API_TOKEN"] = "test-owner-token"
os.environ["JWT_SECRET"] = "test-jwt-secret-not-for-production"
os.environ["SIGNALFLOW_CREDENTIAL_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ["SIGNALFLOW_RETELL_WEBHOOK_SECRET"] = "test-webhook-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models import Base, User, UserRole, VoiceAgent

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

OWNER_HEADERS = {
    "X-Owner-Token": "test-owner-token",
}


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def db():
    with TestingSession() as session:
        yield session


@pytest.fixture
def client():
    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def business_with_agent(client):
    business = client.post("/api/businesses", json={"name": "Alamo Dental"}).json()
    with TestingSession() as session:
        session.add(
            User(
                business_id=business["id"],
                name="Owner",
                email="owner@example.com",
                role=UserRole.owner,
            )
        )
        session.add(
            VoiceAgent(
                business_id=business["id"],
                retell_agent_id="agent-universal-demo",
                retell_agent_name="Universal_Demo",
                name="Universal_Demo",
                greeting="Hello",
                system_prompt="Receptionist",
            )
        )
        session.commit()
    headers = {**OWNER_HEADERS, "X-Business-Id": business["id"]}
    return business, headers


def retell_signature(raw_body: str, api_key: str) -> str:
    timestamp = str(int(time.time() * 1000))
    digest = hmac.new(api_key.encode(), (raw_body + timestamp).encode(), hashlib.sha256).hexdigest()
    return f"v={timestamp},d={digest}"


def legacy_hmac_signature(raw_body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
