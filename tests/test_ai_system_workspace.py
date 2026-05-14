import pytest

from app.models import Entitlement
from app.services.website_scanner_service import PageArtifact, WebsiteScannerService
from tests.conftest import TENANT_ID


@pytest.mark.asyncio
async def test_ai_system_workspace_aggregates_scanner_lifecycle_records(
    client,
    admin_headers,
    db_session,
    monkeypatch,
):
    db_session.add(Entitlement(
        id="ent-workspace-report-generation",
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
                title="WorkspaceBot",
                text=(
                    "WorkspaceBot is an artificial intelligence chatbot and virtual assistant. "
                    "It documents responsible AI, human oversight, audit logs, privacy policy, GDPR, and security."
                ),
                links=[],
            )
        ]

    monkeypatch.setattr(WebsiteScannerService, "validate_public_url", lambda self, url: None)
    monkeypatch.setattr(WebsiteScannerService, "collect_pages", fake_collect_pages)

    scan = client.post(
        "/v1/website-scans",
        headers=admin_headers,
        json={"url": "workspacebot.example"},
    ).json()
    report_response = client.post(f"/v1/website-scans/{scan['id']}/report", headers=admin_headers)
    assert report_response.status_code == 200
    system_id = report_response.json()["ai_system"]["id"]

    response = client.get(f"/v1/ai-systems/{system_id}/workspace", headers=admin_headers)

    assert response.status_code == 200
    workspace = response.json()
    assert workspace["system"]["id"] == system_id
    assert workspace["metrics"]["website_scan_count"] == 1
    assert workspace["metrics"]["control_count"] >= 2
    assert workspace["metrics"]["evidence_log_count"] == 1
    assert workspace["metrics"]["report_count"] == 1
    assert workspace["latest_classification"]["system_classification"] == "Limited Risk AI System"
    assert workspace["website_scans"][0]["id"] == scan["id"]
    assert workspace["reports"][0]["id"] == report_response.json()["report"]["id"]
    assert workspace["evidence_logs"][0]["event_type"] == "website_scan_converted"


def test_ai_system_workspace_respects_tenant_isolation(client, admin_headers, db_session):
    from app.models import AiSystem, Tenant

    db_session.add(Tenant(tenant_id="other-tenant", name="Other Tenant"))
    db_session.add(AiSystem(id="sys-other-workspace", tenant_id="other-tenant", name="Other Workspace"))
    db_session.commit()

    response = client.get("/v1/ai-systems/sys-other-workspace/workspace", headers=admin_headers)

    assert response.status_code == 404
