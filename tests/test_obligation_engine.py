from app.models import IntakeAssessment
from app.services.classification_service import ClassificationService
from app.services.regulatory_knowledge import (
    list_annex_iii_categories,
    list_compliance_dimensions,
    list_penalty_exposures,
    match_annex_iii_categories,
    penalty_exposure_for_dimension,
)


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
    assert provider["penalty_exposure"]["enforcement_article"] == "Article 99(4)"
    assert "applies_when" not in provider


def test_penalty_catalog_maps_articles_to_fine_bands():
    penalties = {item["band_id"]: item for item in list_penalty_exposures()}

    assert penalties["prohibited_practices"]["max_eur"] == 35_000_000
    assert penalties["prohibited_practices"]["turnover_percent"] == 7
    assert penalties["operator_obligations"]["max_eur"] == 15_000_000
    assert penalties["incorrect_information"]["max_eur"] == 7_500_000

    transparency = penalty_exposure_for_dimension("transparency_notice", "Article 50")
    assert transparency["enforcement_article"] == "Article 99(4)"
    assert "EUR 15,000,000" in transparency["maximum_text"]


def test_annex_iii_catalog_and_matcher_map_high_risk_subcategories():
    categories = list_annex_iii_categories()
    ids = {category["subcategory_id"] for category in categories}

    assert "employment_recruitment_selection" in ids
    assert "essential_services_creditworthiness" in ids
    assert "education_test_monitoring" in ids

    matches = match_annex_iii_categories(
        "Our AI screens resumes, ranks candidates for hiring, and supports credit scoring decisions."
    )
    matched_ids = {match["subcategory_id"] for match in matches}

    assert "employment_recruitment_selection" in matched_ids
    assert "essential_services_creditworthiness" in matched_ids
    assert all(match["manual_review_required"] is True for match in matches)


def test_classification_returns_enriched_obligation_graph():
    result = ClassificationService._run_classification_logic({
        "is_deployer": True,
        "is_high_risk_annex_iii": True,
        "has_transparency_obligation": True,
        "is_public_body": True,
        "annex_iii_matches": [{
            "subcategory_id": "essential_services_creditworthiness",
            "annex_ref": "Annex III 5(b)",
            "subcategory": "Creditworthiness or credit scoring",
        }],
    })

    dimensions = {item["dimension_id"]: item for item in result["obligation_graph"]}
    assert dimensions["deployer_high_risk_operations"]["article"] == "Article 26"
    assert dimensions["deployer_high_risk_operations"]["penalty_exposure"]["max_eur"] == 15_000_000
    assert dimensions["fria_screening"]["status"] == "required"
    assert dimensions["transparency_notice"]["article"] == "Article 50"
    assert dimensions["high_risk_classification"]["annex_iii_matches"]
    assert dimensions["deployer_high_risk_operations"]["required_controls"]
    assert dimensions["deployer_high_risk_operations"]["explanation"].startswith("Because")
    assert any(item["dimension_id"] == "fria_screening" for item in result["evidence_requirements"])


def test_obligation_dimensions_endpoint_requires_compliance_scope(client, admin_headers, app_headers):
    denied = client.get("/v1/obligations/dimensions", headers=app_headers)
    assert denied.status_code == 403

    allowed = client.get("/v1/obligations/dimensions", headers=admin_headers)
    assert allowed.status_code == 200
    assert any(item["dimension_id"] == "gpai_provider_obligations" for item in allowed.json())

    annex = client.get("/v1/obligations/annex-iii", headers=admin_headers)
    assert annex.status_code == 200
    assert any(item["subcategory_id"] == "employment_recruitment_selection" for item in annex.json())

    penalties = client.get("/v1/obligations/penalties", headers=admin_headers)
    assert penalties.status_code == 200
    assert any(item["band_id"] == "prohibited_practices" for item in penalties.json())


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
