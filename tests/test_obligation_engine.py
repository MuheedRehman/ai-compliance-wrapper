from app.models import IntakeAssessment
from app.services.classification_service import ClassificationService
from app.services.regulatory_knowledge import list_compliance_dimensions


def test_obligation_dimension_catalog_is_structured():
    dimensions = list_compliance_dimensions()
    ids = {dimension["dimension_id"] for dimension in dimensions}

    assert "ai_literacy" in ids
    assert "provider_high_risk_requirements" in ids
    assert "deployer_high_risk_operations" in ids
    assert "transparency_notice" in ids

    provider = next(item for item in dimensions if item["dimension_id"] == "provider_high_risk_requirements")
    assert provider["articles"]
    assert provider["required_controls"]
    assert provider["required_evidence"]
    assert provider["scanner_signals"]
    assert provider["effective_dates"]
    assert "applies_when" not in provider


def test_classification_returns_enriched_obligation_graph():
    result = ClassificationService._run_classification_logic({
        "is_deployer": True,
        "is_high_risk_annex_iii": True,
        "has_transparency_obligation": True,
        "is_public_body": True,
    })

    dimensions = {item["dimension_id"]: item for item in result["obligation_graph"]}
    assert dimensions["deployer_high_risk_operations"]["article"] == "Article 26"
    assert dimensions["fria_screening"]["status"] == "required"
    assert dimensions["transparency_notice"]["article"] == "Article 50"
    assert dimensions["deployer_high_risk_operations"]["required_controls"]
    assert dimensions["deployer_high_risk_operations"]["explanation"].startswith("Because")
    assert any(item["dimension_id"] == "fria_screening" for item in result["evidence_requirements"])


def test_obligation_dimensions_endpoint_requires_compliance_scope(client, admin_headers, app_headers):
    denied = client.get("/v1/obligations/dimensions", headers=app_headers)
    assert denied.status_code == 403

    allowed = client.get("/v1/obligations/dimensions", headers=admin_headers)
    assert allowed.status_code == 200
    assert any(item["dimension_id"] == "gpai_provider_obligations" for item in allowed.json())


def test_explain_intake_obligations_endpoint(client, admin_headers):
    intake_response = client.post(
        "/v1/intake",
        headers=admin_headers,
        json={
            "title": "Module 4 Explainability Test",
            "answers": {
                "is_deployer": True,
                "is_high_risk_annex_iii": True,
                "has_transparency_obligation": True,
                "fria_required": True,
            },
        },
    )
    assert intake_response.status_code == 200
    intake_id = intake_response.json()["id"]

    explain_response = client.get(f"/v1/obligations/explain/intake/{intake_id}", headers=admin_headers)
    assert explain_response.status_code == 200
    body = explain_response.json()

    assert body["manual_review_required"] is True
    assert body["actor_role"] == "Deployer"
    assert body["system_classification"] == "High-Risk AI System"
    assert any(item["dimension_id"] == "fria_screening" for item in body["applicable_dimensions"])
    assert any(control["control_key"] == "human_oversight_assignment" for control in body["controls_to_create"])
    assert any(evidence["domain"] == "governance_fria" for evidence in body["evidence_requirements"])
    assert all(text.startswith("Because") for text in body["explanations"])


def test_explain_intake_obligations_respects_tenant_isolation(client, admin_headers, db_session):
    other = IntakeAssessment(
        id="intake-other-obligations",
        tenant_id="other-tenant",
        title="Other Tenant Intake",
        answers_json={},
        actor_role="Provider",
        system_classification="Minimal Risk AI System",
        obligation_path="VOLUNTARY_CODE_OF_CONDUCT",
    )
    db_session.add(other)
    db_session.commit()

    response = client.get("/v1/obligations/explain/intake/intake-other-obligations", headers=admin_headers)
    assert response.status_code == 404
