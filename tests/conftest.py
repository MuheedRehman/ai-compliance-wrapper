import os
import sys
import uuid
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

# Ensure test env is set before importing app modules.
os.environ.setdefault("OPENAI_API_KEY", "dummy_test_key")
os.environ.setdefault("DEFAULT_MODEL", "gpt-4.1-nano")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("FEATURE_ID_ENFORCEMENT", "warn")
os.environ.setdefault("CANDIDATE_VERSION_POLICY", "allow_with_warning")
os.environ.setdefault("EVIDENCE_HMAC_SECRET", "test_secret_123456789")

TEST_DB_PATH = Path("app/data/test_app.db")
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_PATH.as_posix()}"

from app.db import Base, engine, SessionLocal, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import ApiKey, AiFeature, Tenant  # noqa: E402
from app.services.hashing import hash_api_key  # noqa: E402


APP_KEY = "aigw_test_app_key_123"
ADMIN_KEY = "aigw_test_admin_key_123"
TENANT_ID = "tenant_test"


def truncate_postgres_tables(db):
    db.execute(text(
        "TRUNCATE TABLE tenant_login_audit, tenant_invitations, tenant_users, tenant_auth_policies, website_scans, compliance_controls, reports, intake_assessments, evidence_items, evidence_bundles, incident_records, oversight_assignments, fria_records, evidence_logs, review_tasks, feature_versions, ai_features, ai_systems, api_keys, tenants RESTART IDENTITY CASCADE"
    ))
    db.commit()


@pytest.fixture(autouse=True)
def reset_database():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if engine.dialect.name == "postgresql":
        db = SessionLocal()
        truncate_postgres_tables(db)
    else:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

    tenant = Tenant(
        tenant_id=TENANT_ID,
        name="Test Tenant",
    )
    db.add(tenant)

    db.add(ApiKey(
        key_id="test_app_key",
        tenant_id=TENANT_ID,
        name="Test App Key",
        key_hash=hash_api_key(APP_KEY),
        role="app",
        scopes=["invoke_ai", "logs:read", "features:read"],
        revoked=False,
    ))

    db.add(ApiKey(
        key_id="test_admin_key",
        tenant_id=TENANT_ID,
        name="Test Admin Key",
        key_hash=hash_api_key(ADMIN_KEY),
        role="admin",
        scopes=[
            "invoke_ai",
            "logs:read",
            "features:read",
            "features:write",
            "reviews:read",
            "reviews:write",
            "intake:read",
            "intake:write",
            "fria:read",
            "fria:write",
            "oversight:read",
            "oversight:write",
            "incidents:read",
            "incidents:write",
            "scanner:read",
            "scanner:write",
            "tenant:read",
            "tenant:admin",
            "tenant:login",
            "admin",
        ],
        revoked=False,
    ))

    db.add(AiFeature(
        id=str(uuid.uuid4()),
        tenant_id=TENANT_ID,
        feature_id="customer_support_bot",
        name="Customer Support Bot",
        slug="customer_support_bot",
        description="Replies to customer support questions.",
        owner_email="founder@example.com",
        team="support",
        use_case="customer_support",
        decision_impact="assistive",
        affected_user_groups=["customers"],
        risk_level_current="low",
        compliance_status="active",
        fria_likely_required=False,
        approved_providers=["openai"],
        approved_models=["gpt-4.1-nano"],
    ))

    db.commit()
    db.close()

    yield

    if engine.dialect.name != "postgresql":
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def app_headers():
    return {"x-api-key": APP_KEY}


@pytest.fixture()
def admin_headers():
    return {"x-api-key": ADMIN_KEY}


@pytest.fixture()
def chat_payload():
    return {
        "model": "gpt-4.1-nano",
        "feature_id": "customer_support_bot",
        "policy_context": {
            "environment": "testing",
            "data_sensitivity": "low",
        },
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful customer support assistant.",
            },
            {
                "role": "user",
                "content": "Write a friendly refund response.",
            },
        ],
        "metadata": {
            "source": "pytest",
        },
    }


@pytest.fixture()
def fake_provider(monkeypatch):
    def fake_call_ai_provider(provider, messages, model, max_tokens):
        return {
            "provider": provider,
            "model": model or "gpt-4.1-nano",
            "output_text": "Here is a friendly refund response.",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18,
            },
            "finish_reason": "stop",
            "provider_response_id": "test_provider_response",
        }

    monkeypatch.setattr("app.services.pipeline.call_ai_provider", fake_call_ai_provider)
    return fake_call_ai_provider


@pytest.fixture()
def failing_provider(monkeypatch):
    def fake_failure(provider, messages, model, max_tokens):
        raise RuntimeError("simulated provider failure")

    monkeypatch.setattr("app.services.pipeline.call_ai_provider", fake_failure)
    return fake_failure
