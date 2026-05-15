import pytest
from fastapi.testclient import TestClient
from app.models import Entitlement, AiSystem, ComplianceControl, ReportRecord, FRIARecord, OversightAssignment
import uuid

@pytest.fixture
def seeded_context(db_session, reset_database):
    # Setup Tenant Context
    tenant_id = "tenant_test"
    
    # Entitlements
    for key in ["report_generation", "fria_management", "oversight_management"]:
        ent = Entitlement(id=str(uuid.uuid4()), tenant_id=tenant_id, feature_key=key, is_enabled=True)
        db_session.add(ent)
    
    # System
    system = AiSystem(id="sys-123", tenant_id=tenant_id, name="Test System")
    db_session.add(system)
    
    # FRIA
    fria = FRIARecord(id="fria-123", tenant_id=tenant_id, ai_system_id="sys-123", status="completed")
    db_session.add(fria)
    
    # Oversight
    ovs = OversightAssignment(id="ovs-123", tenant_id=tenant_id, ai_system_id="sys-123", reviewer_email="test@test.com", role="reviewer")
    db_session.add(ovs)

    for key, article in [
        ("ai_literacy_program", "Article 4"),
        ("deployer_log_retention", "Article 26(6)"),
        ("fria_screening", "Article 27"),
    ]:
        db_session.add(ComplianceControl(
            id=f"ctl-{key}",
            tenant_id=tenant_id,
            ai_system_id="sys-123",
            control_key=key,
            article=article,
            title=key.replace("_", " ").title(),
            status="completed",
            evidence_domain=key,
            details_json={},
        ))
    
    db_session.commit()
    return {"tenant_id": tenant_id, "system_id": "sys-123"}

def test_report_generation(client: TestClient, admin_headers, seeded_context, db_session):
    payload = {
        "report_type": "compliance_readiness_summary",
        "ai_system_id": seeded_context["system_id"],
        "title": "Monthly Readiness Report"
    }
    res = client.post("/v1/reports", json=payload, headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Monthly Readiness Report"
    assert data["report_json"]["readiness_summary"]["status"] == "ready"
    assert any(item["enforcement_article"] == "Article 99(4)" for item in data["report_json"]["penalty_exposures"])
    assert len(data["source_refs_json"]) >= 3 # System, FRIA, Oversight
    assert any(ref["type"] == "compliance_control" for ref in data["source_refs_json"])

def test_report_list_isolation(client: TestClient, admin_headers, seeded_context, db_session):
    # Generate one for tenant_test
    client.post("/v1/reports", json={"report_type": "assessment_summary"}, headers=admin_headers)
    
    # Manually insert one for another tenant
    other = ReportRecord(
        id="rpt-other", 
        tenant_id="other-tenant", 
        report_type="assessment_summary", 
        title="Other Report", 
        report_json={}, 
        source_refs_json=[], 
        artifact_metadata={}
    )
    db_session.add(other)
    db_session.commit()
    
    res = client.get("/v1/reports", headers=admin_headers)
    assert res.status_code == 200
    reports = res.json()
    assert all(r["tenant_id"] == "tenant_test" for r in reports)
    assert "rpt-other" not in [r["id"] for r in reports]

def test_report_detail_and_artifacts(client: TestClient, admin_headers, seeded_context):
    # Create
    res = client.post("/v1/reports", json={"report_type": "assessment_summary"}, headers=admin_headers)
    assert res.status_code == 200
    rpt_id = res.json()["id"]
    
    # Get Detail
    res = client.get(f"/v1/reports/{rpt_id}", headers=admin_headers)
    assert res.status_code == 200
    
    # Download JSON
    res = client.get(f"/v1/reports/{rpt_id}/artifacts/report.json", headers=admin_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/json"
    
    # Download MD
    res = client.get(f"/v1/reports/{rpt_id}/artifacts/report.md", headers=admin_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/markdown")
    assert "# " in res.text # Markdown header

def test_report_cross_tenant_denial(client: TestClient, admin_headers, seeded_context, db_session):
    # Manually insert a report for another tenant
    other = ReportRecord(
        id="rpt-forbidden", 
        tenant_id="other-tenant", 
        report_type="assessment_summary", 
        title="Forbidden Report", 
        report_json={}, 
        source_refs_json=[], 
        artifact_metadata={}
    )
    db_session.add(other)
    db_session.commit()

    # Try to access it with tenant_test headers
    res = client.get("/v1/reports/rpt-forbidden", headers=admin_headers)
    assert res.status_code == 404

def test_missing_entitlement_fails(client: TestClient, admin_headers, db_session, seeded_context):
    # Disable entitlement for the seeded tenant
    ent = db_session.query(Entitlement).filter(
        Entitlement.tenant_id == "tenant_test",
        Entitlement.feature_key == "report_generation"
    ).first()
    if ent:
        ent.is_enabled = False
        db_session.commit()
    
    payload = {"report_type": "assessment_summary"}
    res = client.post("/v1/reports", json=payload, headers=admin_headers)
    assert res.status_code == 403
    assert "not entitled" in res.json()["error"]["message"].lower()
