import pytest
from fastapi.testclient import TestClient
from app.models import IntakeAssessment
from app.services.classification_service import ClassificationService

def test_classification_logic_provider_high_risk():
    answers = {
        "is_developer": True,
        "is_high_risk_annex_iii": True
    }
    result = ClassificationService._run_classification_logic(answers)
    assert result["actor_role"] == "Provider"
    assert result["system_classification"] == "High-Risk AI System"
    assert result["obligation_path"] == "FULL_COMPLIANCE_ART_16"

def test_classification_logic_deployer_high_risk():
    answers = {
        "is_deployer": True,
        "is_high_risk_annex_iii": True
    }
    result = ClassificationService._run_classification_logic(answers)
    assert result["actor_role"] == "Deployer"
    assert result["system_classification"] == "High-Risk AI System"
    assert result["obligation_path"] == "OPERATIONAL_GOVERNANCE_ART_26"
    assert any(item["article"] == "Article 26" for item in result["obligation_graph"])

def test_classification_logic_minimal_risk():
    answers = {
        "is_deployer": True,
        "is_prohibited_use": False,
        "is_high_risk_annex_iii": False,
        "has_transparency_obligation": False
    }
    result = ClassificationService._run_classification_logic(answers)
    assert result["actor_role"] == "Deployer"
    assert result["system_classification"] == "Minimal Risk AI System"
    assert result["obligation_path"] == "VOLUNTARY_CODE_OF_CONDUCT"

def test_create_intake_api(client: TestClient, admin_headers):
    payload = {
        "title": "New System Assessment",
        "answers": {
            "is_developer": True,
            "is_high_risk_annex_iii": True
        }
    }
    response = client.post("/v1/intake", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New System Assessment"
    assert data["actor_role"] == "Provider"
    assert data["obligation_path"] == "FULL_COMPLIANCE_ART_16"
    assert data["legal_basis_json"]
    assert data["obligation_graph_json"]
    assert "id" in data

def test_list_intakes_tenant_isolation(client: TestClient, admin_headers, db_session):
    # Create one for our tenant
    payload = {"title": "T1 Assessment", "answers": {}}
    client.post("/v1/intake", json=payload, headers=admin_headers)
    
    # Create one for another tenant manually
    from app.models import IntakeAssessment
    import uuid
    other_intake = IntakeAssessment(
        id=f"intake-{uuid.uuid4().hex[:8]}",
        tenant_id="other_tenant",
        title="Other Tenant Assessment",
        answers_json={},
        actor_role="Provider",
        system_classification="Minimal",
        obligation_path="NONE"
    )
    db_session.add(other_intake)
    db_session.commit()
    
    response = client.get("/v1/intake", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "T1 Assessment"

def test_get_intake_detail(client: TestClient, admin_headers):
    payload = {"title": "Detail Test", "answers": {"is_gpai": True}}
    create_res = client.post("/v1/intake", json=payload, headers=admin_headers)
    intake_id = create_res.json()["id"]
    
    response = client.get(f"/v1/intake/{intake_id}", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == intake_id
    assert data["system_classification"] == "General Purpose AI (GPAI)"
    assert data["actor_role"] is not None
    assert data["obligation_path"] is not None
    assert data["rationale"] is not None

def test_get_intake_cross_tenant_404(client: TestClient, admin_headers, db_session):
    import uuid
    other_id = f"intake-{uuid.uuid4().hex[:8]}"
    other_intake = IntakeAssessment(
        id=other_id,
        tenant_id="completely_different_tenant",
        title="Secret Assessment",
        answers_json={},
        actor_role="Provider",
        system_classification="Minimal",
        obligation_path="NONE"
    )
    db_session.add(other_intake)
    db_session.commit()

    response = client.get(f"/v1/intake/{other_id}", headers=admin_headers)
    assert response.status_code == 404

def test_classification_logic_ambiguous_precedence():
    # If both are true, Provider should win
    answers = {
        "is_developer": True,
        "is_deployer": True,
        "is_high_risk_annex_iii": True
    }
    result = ClassificationService._run_classification_logic(answers)
    assert result["actor_role"] == "Provider"
    assert result["obligation_path"] == "FULL_COMPLIANCE_ART_16"
    assert "provider" in result["rationale"].lower()

def test_classification_logic_importer_high_risk():
    # If neither developer nor deployer is set, it's Importer/Distributor
    answers = {
        "is_developer": False,
        "is_deployer": False,
        "is_high_risk_annex_iii": True
    }
    result = ClassificationService._run_classification_logic(answers)
    assert result["actor_role"] == "Importer/Distributor"
    assert result["obligation_path"] == "IMPORTER_DISTRIBUTOR_REVIEW_REQUIRED"
    assert "importers and distributors" in result["rationale"].lower()
