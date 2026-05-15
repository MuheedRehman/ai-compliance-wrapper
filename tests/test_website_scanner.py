import pytest

from app.models import ComplianceControl, Entitlement, EvidenceLog, ReportRecord
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
    assert body["confidence_score"] > 50
    assert any(signal["category"] == "high_risk_domain" for signal in body["detected_signals_json"])
    high_risk_gap = next(gap for gap in body["gap_findings_json"] if gap.get("dimension_id") == "high_risk_classification")
    assert high_risk_gap["penalty_exposure"]["enforcement_article"] == "Article 99(4)"
    provider_action = next(action for action in body["suggested_actions_json"] if action.get("dimension_id") == "provider_high_risk_requirements")
    assert provider_action["penalty_exposure"]["max_eur"] == 15_000_000


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
    assert any(ref["type"] == "website_scan" and ref["id"] == scan["id"] for ref in body["report"]["source_refs_json"])
    assert any(ref["type"] == "intake" and ref["id"] == body["intake"]["id"] for ref in body["report"]["source_refs_json"])
    assert any(ref["type"] == "evidence_log" and ref["id"] == body["evidence_event_id"] for ref in body["report"]["source_refs_json"])

    report = db_session.query(ReportRecord).filter(ReportRecord.id == body["report"]["id"]).first()
    assert report is not None
    assert report.ai_system_id == body["ai_system"]["id"]


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
