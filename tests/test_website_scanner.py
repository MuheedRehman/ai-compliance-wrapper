import pytest

from app.models import ComplianceControl, EvidenceLog
from app.services.website_scanner_service import PageArtifact, WebsiteScannerService


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
    assert body["confidence_score"] > 50
    assert any(signal["category"] == "high_risk_domain" for signal in body["detected_signals_json"])


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
