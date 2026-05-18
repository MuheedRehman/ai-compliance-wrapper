import pytest

from app.models import AiSystem, ComplianceControl, Entitlement, EvidenceLog, IntakeAssessment, ReportRecord, WebsiteScan
from app.services.website_scanner_service import PageArtifact, WebsiteScannerService
from tests.conftest import TENANT_ID


@pytest.mark.asyncio
async def test_create_website_scan_detects_ai_and_high_risk(client, admin_headers, monkeypatch):
    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="HirePilot AI",
                text=(
                    "HirePilot AI is an artificial intelligence recruiting assistant. "
                    "It helps with hiring workflows, resume screening, candidate ranking, "
                    "chatbot candidate interactions, "
                    "human oversight, audit logs, privacy policy, GDPR, and security."
                ),
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    response = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "https://hirepilot.example", "max_pages": 4},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["title"] == "HirePilot AI"
    assert body["classification_json"]["risk_level"] == "high"
    assert body["classification_json"]["intake_answers"]["is_high_risk_annex_iii"] is True
    assert body["classification_json"]["canonical_classification"] == "High-Risk AI System"
    assert body["classification_json"]["canonical_obligation_path"] == "FULL_COMPLIANCE_ART_16"
    assert body["classification_json"]["manual_review_required"] is True
    assert body["classification_json"]["legal_basis"]
    annex_matches = {
        match["subcategory_id"]: match
        for match in body["classification_json"]["annex_iii_matches"]
    }
    assert "employment_recruitment_selection" in annex_matches
    assert annex_matches["employment_recruitment_selection"]["annex_ref"] == "Annex III 4(a)"
    assert body["classification_json"]["intake_answers"]["annex_iii_area"] == "employment_recruitment_selection"
    dimensions = {
        dimension["dimension_id"]: dimension
        for dimension in body["classification_json"]["obligation_dimensions"]
    }
    assert dimensions["high_risk_classification"]["article"] == "Article 6 and Annex III"
    assert dimensions["high_risk_classification"]["annex_iii_matches"]
    assert dimensions["high_risk_classification"]["penalty_exposure"]["max_eur"] == 15_000_000
    assert dimensions["provider_high_risk_requirements"]["required_controls"]
    assert dimensions["provider_high_risk_requirements"]["penalty_exposure"]["enforcement_article"] == "Article 99(4)"
    assert dimensions["transparency_notice"]["article"] == "Article 50"
    assert dimensions["transparency_notice"]["matched_public_signals"]
    scenarios = {
        scenario["actor_role"]: scenario
        for scenario in body["classification_json"]["role_scenarios"]
    }
    assert set(scenarios) == {"Provider", "Deployer", "Importer/Distributor"}
    assert scenarios["Provider"]["is_default"] is True
    assert scenarios["Provider"]["obligation_path"] == "FULL_COMPLIANCE_ART_16"
    assert any(
        dimension["dimension_id"] == "provider_high_risk_requirements"
        for dimension in scenarios["Provider"]["obligation_dimensions"]
    )
    assert scenarios["Deployer"]["obligation_path"] == "OPERATIONAL_GOVERNANCE_ART_26"
    assert any(
        dimension["dimension_id"] == "deployer_high_risk_operations"
        for dimension in scenarios["Deployer"]["obligation_dimensions"]
    )
    assert any(
        dimension["dimension_id"] == "fria_screening"
        for dimension in scenarios["Deployer"]["obligation_dimensions"]
    )
    assert scenarios["Importer/Distributor"]["obligation_path"] == "IMPORTER_DISTRIBUTOR_REVIEW_REQUIRED"
    assert any(
        dimension["dimension_id"] == "importer_distributor_verification"
        for dimension in scenarios["Importer/Distributor"]["obligation_dimensions"]
    )
    assert scenarios["Deployer"]["primary_penalty_exposure"]["enforcement_article"] == "Article 99(4)"
    assert body["confidence_score"] > 50
    assert any(signal["category"] == "high_risk_domain" for signal in body["detected_signals_json"])
    high_risk_gap = next(gap for gap in body["gap_findings_json"] if gap.get("dimension_id") == "high_risk_classification")
    assert high_risk_gap["penalty_exposure"]["enforcement_article"] == "Article 99(4)"
    provider_action = next(action for action in body["suggested_actions_json"] if action.get("dimension_id") == "provider_high_risk_requirements")
    assert provider_action["penalty_exposure"]["max_eur"] == 15_000_000


@pytest.mark.asyncio
async def test_website_scan_extracts_public_evidence_profile_and_richer_gaps(client, admin_headers, monkeypatch):
    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="AssessPro AI",
                text=(
                    "AssessPro AI uses artificial intelligence for credit scoring and loan eligibility. "
                    "It ranks applicants automatically. Model limitations and accuracy warnings may apply."
                ),
                links=[],
            ),
            PageArtifact(
                url=f"{normalized_url.rstrip('/')}/privacy",
                status_code=200,
                title="Privacy",
                text="Privacy policy, GDPR, data processing, DPA, subprocessors, and data retention are documented.",
                links=[],
            ),
            PageArtifact(
                url=f"{normalized_url.rstrip('/')}/security",
                status_code=200,
                title="Security",
                text="Security controls include SOC 2, ISO 27001, encryption, and vulnerability management.",
                links=[],
            ),
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    response = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "https://assesspro.example", "max_pages": 4},
    )

    assert response.status_code == 200
    body = response.json()
    profile = body["classification_json"]["public_evidence_profile"]
    assert profile["coverage"]["data_governance"] is True
    assert profile["coverage"]["security_certification"] is True
    assert profile["coverage"]["limitations_accuracy"] is True
    assert profile["coverage"]["human_oversight"] is False
    assert profile["coverage_score"] > 40
    assert any(ref["type"] == "public_evidence_topic" for ref in body["evidence_refs_json"])
    assert any("data_governance" in page["evidence_topics"] for page in body["source_pages_json"])

    gap_titles = {gap["title"] for gap in body["gap_findings_json"]}
    assert "User-facing AI disclosure evidence not found" in gap_titles
    assert "Human oversight evidence missing for high-risk triage" in gap_titles
    assert "Logging or incident process evidence missing" in gap_titles


@pytest.mark.asyncio
async def test_convert_website_scan_creates_system_and_intake(client, admin_headers, monkeypatch):
    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="SupportBot",
                text="SupportBot is an AI chatbot and virtual assistant for customer support with a privacy policy.",
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "supportbot.example"},
    ).json()

    response = client.post(f"/v1/website-scans/{scan['id']}/convert", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["ai_system"]["name"] == "SupportBot"
    assert body["intake"]["system_classification"] == "Limited Risk AI System"
    assert body["scan"]["ai_system_id"] == body["ai_system"]["id"]
    assert body["scan"]["intake_id"] == body["intake"]["id"]
    assert len(body["controls"]) >= 2
    assert body["evidence_event_id"]


@pytest.mark.asyncio
async def test_convert_website_scan_uses_selected_role_scenario(client, admin_headers, db_session, monkeypatch):
    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="HireOps AI",
                text=(
                    "HireOps AI is an artificial intelligence recruiting and hiring platform. "
                    "It performs resume screening, candidate ranking, chatbot interviews, "
                    "human oversight, audit logs, privacy policy, GDPR, and security."
                ),
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "hireops.example"},
    ).json()

    response = client.post(
        f"/v1/website-scans/{scan['id']}/convert",
        headers=admin_headers,
        json={"actor_role": "Deployer"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intake"]["actor_role"] == "Deployer"
    assert body["intake"]["obligation_path"] == "OPERATIONAL_GOVERNANCE_ART_26"
    assert body["intake"]["answers_json"]["selected_actor_role"] == "Deployer"
    assert body["scan"]["classification_json"]["selected_actor_role"] == "Deployer"
    assert any(
        item["dimension_id"] == "deployer_high_risk_operations"
        for item in body["intake"]["obligation_graph_json"]
    )
    assert any(
        item["dimension_id"] == "fria_screening"
        for item in body["intake"]["obligation_graph_json"]
    )

    controls = db_session.query(ComplianceControl).filter(
        ComplianceControl.ai_system_id == body["ai_system"]["id"],
    ).all()
    control_keys = {control.control_key for control in controls}
    assert "intake_deployer_high_risk_operations" in control_keys
    assert "intake_provider_high_risk_requirements" not in control_keys

    conflict = client.post(
        f"/v1/website-scans/{scan['id']}/convert",
        headers=admin_headers,
        json={"actor_role": "Provider"},
    )
    assert conflict.status_code == 409


@pytest.mark.asyncio
async def test_convert_website_scan_materializes_controls_and_evidence_once(
    client,
    admin_headers,
    db_session,
    monkeypatch,
):
    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="CreditScore AI",
                text=(
                    "CreditScore AI is an artificial intelligence lending and credit scoring platform. "
                    "It uses model cards, audit logs, responsible AI review, privacy policy, and SOC 2 security."
                ),
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "creditscore.example"},
    ).json()

    first = client.post(f"/v1/website-scans/{scan['id']}/convert", headers=admin_headers)
    second = client.post(f"/v1/website-scans/{scan['id']}/convert", headers=admin_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    first_body = first.json()
    second_body = second.json()

    assert first_body["scan"]["ai_system_id"] == second_body["scan"]["ai_system_id"]
    assert first_body["intake"]["id"] == second_body["intake"]["id"]
    assert first_body["evidence_event_id"] == second_body["evidence_event_id"]

    controls = db_session.query(ComplianceControl).filter(
        ComplianceControl.ai_system_id == first_body["ai_system"]["id"],
    ).all()
    evidence_logs = db_session.query(EvidenceLog).filter(
        EvidenceLog.ai_system_id == first_body["ai_system"]["id"],
        EvidenceLog.event_type == "website_scan_converted",
    ).all()

    assert len(controls) == len(first_body["controls"])
    assert len(evidence_logs) == 1
    assert evidence_logs[0].evidence_domain == "website_scan"
    assert evidence_logs[0].request_metadata["scan_id"] == scan["id"]


def test_website_scan_requires_admin_scope(client, app_headers):
    response = client.get("/v1/website-scans", headers=app_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_generate_website_scan_report_converts_scan_and_links_sources(
    client,
    admin_headers,
    db_session,
    monkeypatch,
):
    db_session.add(Entitlement(
        id="ent-report-generation",
        tenant_id=TENANT_ID,
        feature_key="report_generation",
        is_enabled=True,
    ))
    db_session.commit()

    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="Assistly AI",
                text=(
                    "Assistly AI is an artificial intelligence chatbot and virtual assistant. "
                    "It discloses responsible AI practices, human oversight, audit logs, privacy policy, and GDPR."
                ),
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "assistly.example"},
    ).json()

    response = client.post(f"/v1/website-scans/{scan['id']}/report", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["scan"]["ai_system_id"] == body["ai_system"]["id"]
    assert body["scan"]["intake_id"] == body["intake"]["id"]
    assert body["controls"]
    assert body["evidence_event_id"]
    assert body["report"]["report_type"] == "compliance_readiness_summary"
    assert body["report"]["ai_system_id"] == body["ai_system"]["id"]
    audit_pack = body["report"]["report_json"]["scanner_audit_pack"]
    assert audit_pack["summary"]["scan_count"] == 1
    assert audit_pack["summary"]["found_topic_count"] >= 3
    assert audit_pack["summary"]["average_public_evidence_coverage"] > 0
    assert any(topic["topic"] == "human_oversight" for topic in audit_pack["found_topics"])
    assert any(topic["topic"] == "logging_monitoring" for topic in audit_pack["found_topics"])
    assert any(source["url"] == scan["normalized_url"] for source in audit_pack["public_sources"])
    assert any(
        finding["title"].startswith("Scanner gap:")
        for finding in body["report"]["report_json"]["findings"]
    )
    assert any(ref["type"] == "website_scan" and ref["id"] == scan["id"] for ref in body["report"]["source_refs_json"])
    assert any(ref["type"] == "intake" and ref["id"] == body["intake"]["id"] for ref in body["report"]["source_refs_json"])
    assert any(ref["type"] == "evidence_log" and ref["id"] == body["evidence_event_id"] for ref in body["report"]["source_refs_json"])

    report = db_session.query(ReportRecord).filter(ReportRecord.id == body["report"]["id"]).first()
    assert report is not None
    assert report.ai_system_id == body["ai_system"]["id"]

    artifact = client.get(f"/v1/reports/{body['report']['id']}/artifacts/report.md", headers=admin_headers)
    assert artifact.status_code == 200
    assert "## Website Scanner Audit Pack" in artifact.text
    assert "Public evidence coverage" in artifact.text


@pytest.mark.asyncio
async def test_generate_website_scan_report_requires_report_entitlement(
    client,
    admin_headers,
    monkeypatch,
):
    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="NoEntitlement AI",
                text="NoEntitlement AI is an artificial intelligence chatbot with a privacy policy.",
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "no-entitlement.example"},
    ).json()

    response = client.post(f"/v1/website-scans/{scan['id']}/report", headers=admin_headers)

    assert response.status_code == 403
    assert "not entitled" in response.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_generate_website_scan_report_rolls_back_conversion_on_report_failure(
    client,
    admin_headers,
    db_session,
    monkeypatch,
):
    db_session.add(Entitlement(
        id="ent-report-rollback",
        tenant_id=TENANT_ID,
        feature_key="report_generation",
        is_enabled=True,
    ))
    db_session.commit()

    async def fake_collect_pages(self, normalized_url, max_pages):
        return [
            PageArtifact(
                url=normalized_url,
                status_code=200,
                title="Rollback AI",
                text="Rollback AI is an artificial intelligence chatbot with human oversight, audit logs, and privacy policy.",
                links=[],
            )
        ]

    def fail_report(*args, **kwargs):
        raise RuntimeError("simulated report failure")

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)
    monkeypatch.setattr("app.routes.website_scans.ReportService.generate_report", fail_report)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "rollback.example"},
    ).json()

    with pytest.raises(RuntimeError, match="simulated report failure"):
        client.post(f"/v1/website-scans/{scan['id']}/report", headers=admin_headers)

    db_session.expire_all()
    persisted_scan = db_session.query(WebsiteScan).filter(WebsiteScan.id == scan["id"]).first()
    assert persisted_scan is not None
    assert persisted_scan.ai_system_id is None
    assert persisted_scan.intake_id is None
    assert db_session.query(AiSystem).filter(AiSystem.name == "Rollback AI").count() == 0
    assert db_session.query(IntakeAssessment).count() == 0
    assert db_session.query(ComplianceControl).count() == 0
    assert db_session.query(EvidenceLog).filter(EvidenceLog.event_type == "website_scan_converted").count() == 0
    assert db_session.query(ReportRecord).count() == 0
