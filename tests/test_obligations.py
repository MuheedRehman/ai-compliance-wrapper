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


# --- Module 7: FRIA Builder workflow tests ---

def _create_fria(client, system_id, headers):
    res = client.post("/v1/obligations/fria", json={"ai_system_id": system_id}, headers=headers)
    assert res.status_code == 200
    return res.json()["id"]


def test_fria_sections_update_and_completion(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)

    # Initially 0% complete and new response fields present
    res = client.get(f"/v1/obligations/fria/{fria_id}", headers=admin_headers)
    data = res.json()
    assert data["completion_percent"] == 0
    assert data["sections_json"] == {}
    assert data["approval_json"] == {}

    # Save two sections
    sections = {
        "intended_purpose": {
            "system_description": "Credit scoring AI for loan applications",
            "deployment_context": "Retail banking",
            "intended_users": "Loan officers",
            "geographic_scope": "EU",
        },
        "affected_persons": {
            "population_description": "Adult loan applicants",
            "vulnerable_groups": "Low-income individuals",
            "estimated_scale": "50,000 per year",
            "interaction_type": "Indirect automated decision",
        },
    }
    res = client.patch(f"/v1/obligations/fria/{fria_id}/sections", json=sections, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["completion_percent"] == round(2 / 6 * 100)
    assert data["sections_json"]["intended_purpose"]["system_description"] == "Credit scoring AI for loan applications"

    # Saving remaining 4 sections brings completion to 100%
    remaining = {
        "fundamental_rights_risks": {
            "rights_at_risk": "Right to non-discrimination, right to explanation",
            "risk_descriptions": "Potential bias against protected groups",
            "severity_assessment": "High",
            "likelihood_assessment": "Medium",
        },
        "mitigation_measures": {
            "technical_measures": "Bias audits, SHAP explainability",
            "organizational_measures": "Annual third-party audit",
            "human_oversight_measures": "Loan officer can override",
            "monitoring_approach": "Monthly fairness metrics review",
        },
        "human_oversight": {
            "oversight_roles": "Chief Risk Officer, Compliance Manager",
            "oversight_procedures": "Quarterly review board",
            "override_capability": "Full manual override by loan officer",
            "escalation_path": "DPO → Legal → Board",
        },
        "residual_risk": {
            "remaining_risks": "Residual proxy discrimination possible",
            "risk_acceptance_rationale": "Risk mitigated to acceptable level with controls",
            "review_schedule": "Annual",
            "dpo_consulted": "Yes, consulted 2026-01-15",
        },
    }
    res = client.patch(f"/v1/obligations/fria/{fria_id}/sections", json=remaining, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["completion_percent"] == 100


def test_fria_approval_workflow(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)

    # Submit for review
    res = client.post(
        f"/v1/obligations/fria/{fria_id}/submit",
        json={"submitted_by": "compliance@example.com"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "in_review"
    assert data["approval_json"]["submitted_by"] == "compliance@example.com"
    assert data["approval_json"]["outcome"] is None

    # Cannot edit sections while in_review
    res = client.patch(
        f"/v1/obligations/fria/{fria_id}/sections",
        json={"intended_purpose": {"system_description": "blocked"}},
        headers=admin_headers,
    )
    assert res.status_code == 409

    # Cannot submit again
    res = client.post(
        f"/v1/obligations/fria/{fria_id}/submit",
        json={"submitted_by": "compliance@example.com"},
        headers=admin_headers,
    )
    assert res.status_code == 409

    # Approve
    res = client.post(
        f"/v1/obligations/fria/{fria_id}/review",
        json={"reviewer_email": "dpo@example.com", "outcome": "approved", "notes": "Looks good"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["approval_json"]["reviewed_by"] == "dpo@example.com"
    assert data["approval_json"]["outcome"] == "approved"


def test_fria_rejection_allows_resubmission(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)

    # Submit then reject
    client.post(f"/v1/obligations/fria/{fria_id}/submit", json={"submitted_by": "x@x.com"}, headers=admin_headers)
    res = client.post(
        f"/v1/obligations/fria/{fria_id}/review",
        json={"reviewer_email": "dpo@x.com", "outcome": "rejected", "notes": "Needs more detail"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"

    # Rejected FRIAs can have sections edited without reverting to draft
    res = client.patch(
        f"/v1/obligations/fria/{fria_id}/sections",
        json={"intended_purpose": {"system_description": "Updated after rejection", "deployment_context": "ctx", "intended_users": "users", "geographic_scope": "EU"}},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["sections_json"]["intended_purpose"]["system_description"] == "Updated after rejection"

    # Can resubmit directly from rejected state (no manual draft reset required)
    res = client.post(f"/v1/obligations/fria/{fria_id}/submit", json={"submitted_by": "x@x.com"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "in_review"


def test_fria_approved_cannot_be_deleted(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)
    client.post(f"/v1/obligations/fria/{fria_id}/submit", json={"submitted_by": "x@x.com"}, headers=admin_headers)
    client.post(
        f"/v1/obligations/fria/{fria_id}/review",
        json={"reviewer_email": "dpo@x.com", "outcome": "approved", "notes": ""},
        headers=admin_headers,
    )
    res = client.delete(f"/v1/obligations/fria/{fria_id}", headers=admin_headers)
    assert res.status_code == 409
    assert "cannot be deleted" in res.json()["error"]["message"]


def test_fria_response_includes_system_name(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)

    # Single get
    res = client.get(f"/v1/obligations/fria/{fria_id}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["ai_system_name"] == seeded_system.name

    # List
    res = client.get("/v1/obligations/fria", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()[0]["ai_system_name"] == seeded_system.name


def test_fria_review_invalid_outcome(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)
    client.post(f"/v1/obligations/fria/{fria_id}/submit", json={"submitted_by": "x@x.com"}, headers=admin_headers)
    res = client.post(
        f"/v1/obligations/fria/{fria_id}/review",
        json={"reviewer_email": "dpo@x.com", "outcome": "pending"},
        headers=admin_headers,
    )
    assert res.status_code == 422


def test_fria_export_markdown(client: TestClient, admin_headers, seeded_system, seeded_entitlements):
    fria_id = _create_fria(client, seeded_system.id, admin_headers)
    client.patch(
        f"/v1/obligations/fria/{fria_id}/sections",
        json={
            "intended_purpose": {
                "system_description": "Recruitment AI",
                "deployment_context": "HR",
                "intended_users": "HR managers",
                "geographic_scope": "EU",
            }
        },
        headers=admin_headers,
    )
    res = client.get(f"/v1/obligations/fria/{fria_id}/export", headers=admin_headers)
    assert res.status_code == 200
    assert "Fundamental Rights Impact Assessment" in res.text
    assert "Recruitment AI" in res.text
    assert "Article 27" in res.text

def test_evidence_domain_verification(client: TestClient, admin_headers, seeded_system, seeded_entitlements, db_session):
    from app.models import EvidenceLog
    # Trigger FRIA creation (logs evidence)
    payload = {"ai_system_id": seeded_system.id, "assessment_json": {}, "status": "draft"}
    client.post("/v1/obligations/fria", json=payload, headers=admin_headers)
    
    # Check EvidenceLog
    logs = db_session.query(EvidenceLog).filter(EvidenceLog.evidence_domain == "governance_fria").all()
    assert len(logs) >= 1
    assert logs[0].event_type == "fria_created"
