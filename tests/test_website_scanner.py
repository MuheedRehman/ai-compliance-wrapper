import pytest

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


def test_website_scan_requires_admin_scope(client, app_headers):
    response = client.get("/v1/website-scans", headers=app_headers)
    assert response.status_code == 403
