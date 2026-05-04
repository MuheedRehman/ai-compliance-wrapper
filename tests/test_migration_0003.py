import uuid
import pytest
from sqlalchemy import inspect
from app.models import AiSystem, AiFeature, EvidenceLog, ReviewTask, FRIARecord, OversightAssignment, IncidentRecord, EvidenceBundle
from app.db import SessionLocal

def test_migration_0003_tables_exist(db_session):
    inspector = inspect(db_session.get_bind())
    tables = inspector.get_table_names()
    
    expected_tables = [
        "ai_systems",
        "fria_records",
        "oversight_assignments",
        "incident_records",
        "evidence_bundles"
    ]
    for table in expected_tables:
        assert table in tables, f"Table {table} missing after migration"

def test_migration_0003_columns_and_nullability(db_session):
    inspector = inspect(db_session.get_bind())
    
    # Check AiFeature
    cols = {c["name"]: c for c in inspector.get_columns("ai_features")}
    assert "ai_system_id" in cols
    assert cols["ai_system_id"]["nullable"] is True
    
    # Check EvidenceLog
    cols = {c["name"]: c for c in inspector.get_columns("evidence_logs")}
    assert "ai_system_id" in cols
    assert cols["ai_system_id"]["nullable"] is True
    assert "evidence_domain" in cols
    assert cols["evidence_domain"]["nullable"] is True
    
    # Check ReviewTask
    cols = {c["name"]: c for c in inspector.get_columns("review_tasks")}
    assert "ai_system_id" in cols
    assert cols["ai_system_id"]["nullable"] is True

def test_pipeline_works_with_unlinked_feature(client, chat_payload, fake_provider, db_session):
    # Ensure a feature exists (fixture does this)
    response = client.post("/v1/chat/completions", json=chat_payload, headers={"x-api-key": "aigw_test_app_key_123"})
    assert response.status_code == 200
    
    # Verify evidence has NULL ai_system_id
    evidence = db_session.query(EvidenceLog).first()
    assert evidence is not None
    assert evidence.ai_system_id is None

def test_ai_system_creation(db_session):
    system_id = str(uuid.uuid4())
    system = AiSystem(
        id=system_id,
        tenant_id="tenant_test",
        name="Test System",
        description="A test system",
        deployment_status="draft",
        registration_status="draft"
    )
    db_session.add(system)
    db_session.commit()
    
    queried = db_session.query(AiSystem).filter_by(id=system_id).first()
    assert queried is not None
    assert queried.name == "Test System"
    assert queried.deployment_status == "draft"
