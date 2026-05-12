import pytest
from fastapi.testclient import TestClient
from app.models import Entitlement, AiSystem
import uuid

@pytest.fixture
def seeded_system(db_session, reset_database):
    system = AiSystem(
        id=f"sys-{uuid.uuid4().hex[:8]}",
        tenant_id="tenant_test",
        name="Test AI System"
    )
    db_session.add(system)
    db_session.commit()
    return system

@pytest.fixture
def seeded_entitlements(db_session):
    for key in ["fria_management", "oversight_management", "incident_management"]:
        ent = Entitlement(
            id=str(uuid.uuid4()),
            tenant_id="tenant_test",
            feature_key=key,
            is_enabled=True
        )
        db_session.add(ent)
    db_session.commit()

def test_fria_crud(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    # Create
    payload = {
        "ai_system_id": seeded_system.id,
        "assessment_json": {"risk": "high"},
        "status": "draft"
    }
    res = client.post("/v1/obligations/fria", json=payload, headers=admin_headers)
    assert res.status_code == 200
    fria_id = res.json()["id"]
    assert res.json()["legal_basis_json"][0]["article"] == "Article 27"

    # List
    res = client.get("/v1/obligations/fria", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Get
    res = client.get(f"/v1/obligations/fria/{fria_id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["assessment_json"]["risk"] == "high"

    # Update
    res = client.patch(f"/v1/obligations/fria/{fria_id}", json={"status": "completed"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "completed"

    # Delete
    res = client.delete(f"/v1/obligations/fria/{fria_id}", headers=admin_headers)
    assert res.status_code == 200

def test_oversight_crud(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    # Create
    payload = {
        "ai_system_id": seeded_system.id,
        "reviewer_email": "oversight@example.com",
        "role": "technical_reviewer"
    }
    res = client.post("/v1/obligations/oversight", json=payload, headers=admin_headers)
    assert res.status_code == 200
    assignment_id = res.json()["id"]

    # List
    res = client.get("/v1/obligations/oversight", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Update
    res = client.patch(f"/v1/obligations/oversight/{assignment_id}", json={"role": "senior_reviewer"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["role"] == "senior_reviewer"

    # Delete
    res = client.delete(f"/v1/obligations/oversight/{assignment_id}", headers=admin_headers)
    assert res.status_code == 200

def test_incident_crud(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    # Create
    payload = {
        "ai_system_id": seeded_system.id,
        "severity": "high",
        "description": "Data leak in production",
        "incident_type": "widespread_infringement",
        "status": "open"
    }
    res = client.post("/v1/obligations/incidents", json=payload, headers=admin_headers)
    assert res.status_code == 200
    incident_id = res.json()["id"]
    assert res.json()["deadline_at"] is not None
    assert res.json()["incident_type"] == "widespread_infringement"

    # List
    res = client.get("/v1/obligations/incidents", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Get
    res = client.get(f"/v1/obligations/incidents/{incident_id}", headers=admin_headers)
    assert res.status_code == 200

    # Update
    res = client.patch(f"/v1/obligations/incidents/{incident_id}", json={"status": "resolved"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "resolved"

    # Delete
    res = client.delete(f"/v1/obligations/incidents/{incident_id}", headers=admin_headers)
    assert res.status_code == 200

def test_fria_entitlement_gating(client: TestClient, admin_headers, seeded_system):
    # No entitlements seeded for this test
    payload = {
        "ai_system_id": seeded_system.id,
        "assessment_json": {},
        "status": "draft"
    }
    res = client.post("/v1/obligations/fria", json=payload, headers=admin_headers)
    assert res.status_code == 403
    assert "not entitled" in res.json()["error"]["message"]

def test_fria_tenant_isolation(client: TestClient, admin_headers, seeded_system, seeded_entitlements, db_session):
    from app.models import FRIARecord
    # Create a record for our tenant
    payload = {"ai_system_id": seeded_system.id, "assessment_json": {}}
    client.post("/v1/obligations/fria", json=payload, headers=admin_headers)

    # Manually insert a record for another tenant
    other_fria = FRIARecord(
        id="fria-other",
        tenant_id="other-tenant",
        ai_system_id="other-sys",
        assessment_json={}
    )
    db_session.add(other_fria)
    db_session.commit()

    # List should only show ours
    res = client.get("/v1/obligations/fria", headers=admin_headers)
    assert res.status_code == 200
    assert len(res.json()) == 1

    # Direct access to other tenant's record should fail
    res = client.get("/v1/obligations/fria/fria-other", headers=admin_headers)
    assert res.status_code == 404

def test_fria_rejects_foreign_system_id(client: TestClient, admin_headers, seeded_entitlements, db_session):
    from app.models import AiSystem, Tenant
    db_session.add(Tenant(tenant_id="other-tenant", name="Other Tenant"))
    db_session.add(AiSystem(id="other-sys", tenant_id="other-tenant", name="Other System"))
    db_session.commit()

    res = client.post(
        "/v1/obligations/fria",
        json={"ai_system_id": "other-sys", "assessment_json": {}},
        headers=admin_headers,
    )
    assert res.status_code == 404

def test_oversight_entitlement_gating(client: TestClient, admin_headers, seeded_system):
    payload = {"ai_system_id": seeded_system.id, "reviewer_email": "test@test.com", "role": "test"}
    res = client.post("/v1/obligations/oversight", json=payload, headers=admin_headers)
    assert res.status_code == 403

def test_incident_entitlement_gating(client: TestClient, admin_headers, seeded_system):
    payload = {"ai_system_id": seeded_system.id, "severity": "low", "description": "test"}
    res = client.post("/v1/obligations/incidents", json=payload, headers=admin_headers)
    assert res.status_code == 403

def test_oversight_tenant_isolation(client: TestClient, admin_headers, seeded_system, seeded_entitlements, db_session):
    from app.models import OversightAssignment
    # Ours
    payload = {"ai_system_id": seeded_system.id, "reviewer_email": "ours@test.com", "role": "ours"}
    client.post("/v1/obligations/oversight", json=payload, headers=admin_headers)
    
    # Theirs
    other = OversightAssignment(id="ovs-other", tenant_id="other-tenant", ai_system_id="other-sys", reviewer_email="theirs@test.com", role="theirs")
    db_session.add(other)
    db_session.commit()
    
    res = client.get("/v1/obligations/oversight", headers=admin_headers)
    assert len(res.json()) == 1
    res = client.delete("/v1/obligations/oversight/ovs-other", headers=admin_headers)
    assert res.status_code == 404

def test_incident_tenant_isolation(client: TestClient, admin_headers, seeded_system, seeded_entitlements, db_session):
    from app.models import IncidentRecord
    # Ours
    payload = {"ai_system_id": seeded_system.id, "severity": "low", "description": "ours"}
    client.post("/v1/obligations/incidents", json=payload, headers=admin_headers)
    
    # Theirs
    other = IncidentRecord(id="inc-other", tenant_id="other-tenant", ai_system_id="other-sys", severity="high", description="theirs")
    db_session.add(other)
    db_session.commit()
    
    res = client.get("/v1/obligations/incidents", headers=admin_headers)
    assert len(res.json()) == 1
    res = client.get("/v1/obligations/incidents/inc-other", headers=admin_headers)
    assert res.status_code == 404

def test_evidence_domain_verification(client: TestClient, admin_headers, seeded_system, seeded_entitlements, db_session):
    from app.models import EvidenceLog
    # Trigger FRIA creation (logs evidence)
    payload = {"ai_system_id": seeded_system.id, "assessment_json": {}, "status": "draft"}
    client.post("/v1/obligations/fria", json=payload, headers=admin_headers)
    
    # Check EvidenceLog
    logs = db_session.query(EvidenceLog).filter(EvidenceLog.evidence_domain == "governance_fria").all()
    assert len(logs) >= 1
    assert logs[0].event_type == "fria_created"
