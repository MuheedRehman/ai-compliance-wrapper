import pytest
from datetime import datetime, timedelta, timezone

from app.models import AiSystem, ComplianceControl, Entitlement, EvidenceItem, ReviewTask, Tenant
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
    db_session.add(Tenant(tenant_id="other-tenant", name="Other Tenant"))
    db_session.add(AiSystem(id="sys-other-workspace", tenant_id="other-tenant", name="Other Workspace"))
    db_session.commit()

    response = client.get("/v1/ai-systems/sys-other-workspace/workspace", headers=admin_headers)

    assert response.status_code == 404


def test_ai_system_lifecycle_owners_deadline_and_review_history(client, admin_headers):
    next_review = datetime.now(timezone.utc) + timedelta(days=14)
    response = client.post(
        "/v1/ai-systems",
        headers=admin_headers,
        json={
            "name": "Lifecycle System",
            "description": "Operational workspace test",
            "owner_email": "Business.Owner@Example.com",
            "technical_owner_email": "Tech.Owner@Example.com",
            "review_status": "scheduled",
            "next_review_at": next_review.isoformat(),
            "lifecycle_notes": "Review quarterly before release expansion.",
        },
    )

    assert response.status_code == 200
    system = response.json()
    system_id = system["id"]
    assert system["owner_email"] == "business.owner@example.com"
    assert system["technical_owner_email"] == "tech.owner@example.com"
    assert system["legal_owner_email"] is None
    assert system["review_status"] == "scheduled"
    assert system["next_review_at"] is not None

    control_response = client.post(
        "/v1/compliance/controls",
        headers=admin_headers,
        json={
            "ai_system_id": system_id,
            "control_key": "review_follow_up_control",
            "article": "Article 9",
            "title": "Review follow-up risk control",
            "evidence_domain": "risk_management",
        },
    )
    assert control_response.status_code == 200
    control_id = control_response.json()["id"]

    review_next = datetime.now(timezone.utc) + timedelta(days=60)
    review_response = client.post(
        f"/v1/ai-systems/{system_id}/reviews",
        headers=admin_headers,
        json={
            "reviewer_email": "Reviewer@Example.com",
            "review_type": "classification_review",
            "status": "completed",
            "notes": "Classification and control linkage reviewed.",
            "findings": [{"severity": "low", "summary": "Refresh evidence before launch."}],
            "actions": [{
                "title": "Attach updated DPIA",
                "owner_email": "legal@example.com",
                "target_type": "control",
                "control_id": control_id,
                "severity": "high",
            }],
            "next_review_at": review_next.isoformat(),
        },
    )

    assert review_response.status_code == 200
    review = review_response.json()
    assert review["reviewer_email"] == "reviewer@example.com"
    assert review["review_type"] == "classification_review"
    assert review["status"] == "completed"
    assert review["findings_json"][0]["summary"] == "Refresh evidence before launch."
    assert review["actions_json"][0]["target_type"] == "control"
    assert review["actions_json"][0]["control_id"] == control_id
    assert review["actions_json"][0]["review_task_id"]

    get_response = client.get(f"/v1/ai-systems/{system_id}", headers=admin_headers)
    updated_system = get_response.json()
    assert updated_system["review_status"] == "completed"
    assert updated_system["last_reviewed_at"] is not None
    assert updated_system["next_review_at"] is not None

    reviews_response = client.get(f"/v1/ai-systems/{system_id}/reviews", headers=admin_headers)
    assert reviews_response.status_code == 200
    assert len(reviews_response.json()) == 1

    workspace_response = client.get(f"/v1/ai-systems/{system_id}/workspace", headers=admin_headers)
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()
    assert workspace["metrics"]["review_event_count"] == 1
    assert workspace["metrics"]["follow_up_task_count"] == 1
    assert workspace["metrics"]["open_follow_up_task_count"] == 1
    assert workspace["metrics"]["linked_follow_up_task_count"] == 1
    assert workspace["metrics"]["assigned_owner_count"] == 2
    assert workspace["governance_summary"]["missing_owner_roles"] == ["legal_owner"]
    assert workspace["governance_summary"]["review_deadline_status"] == "scheduled"
    assert workspace["review_events"][0]["id"] == review["id"]
    follow_up = workspace["follow_up_tasks"][0]
    assert follow_up["ai_system_id"] == system_id
    assert follow_up["review_type"] == "ai_system_lifecycle_follow_up"
    assert follow_up["severity"] == "high"
    assert follow_up["findings_json"]["source_review_event_id"] == review["id"]
    assert follow_up["findings_json"]["control_id"] == control_id

    close_response = client.patch(
        f"/v1/review-tasks/{follow_up['review_task_id']}/close",
        headers=admin_headers,
        json={"resolution_note": "Resolved from workspace"},
    )
    assert close_response.status_code == 200
    assert close_response.json()["status"] == "closed"

    closed_workspace = client.get(f"/v1/ai-systems/{system_id}/workspace", headers=admin_headers).json()
    assert closed_workspace["metrics"]["follow_up_task_count"] == 1
    assert closed_workspace["metrics"]["open_follow_up_task_count"] == 0


def test_ai_system_review_multi_action_plan_creates_control_and_evidence_placeholders(
    client,
    admin_headers,
    db_session,
):
    system_response = client.post(
        "/v1/ai-systems",
        headers=admin_headers,
        json={"name": "Action Plan System"},
    )
    assert system_response.status_code == 200
    system_id = system_response.json()["id"]
    due_at = (datetime.now(timezone.utc) + timedelta(days=21)).isoformat()

    review_response = client.post(
        f"/v1/ai-systems/{system_id}/reviews",
        headers=admin_headers,
        json={
            "reviewer_email": "owner@example.com",
            "review_type": "control_review",
            "status": "needs_follow_up",
            "actions": [
                {
                    "title": "Create bias testing control",
                    "target_type": "control",
                    "owner_email": "control.owner@example.com",
                    "due_at": due_at,
                    "severity": "critical",
                    "article": "Article 10",
                    "evidence_domain": "bias_testing",
                },
                {
                    "title": "Collect model card evidence",
                    "target_type": "evidence",
                    "owner_email": "evidence.owner@example.com",
                    "due_at": due_at,
                    "severity": "medium",
                    "evidence_type": "model_card",
                },
                {
                    "title": "Schedule stakeholder review",
                    "target_type": "general",
                    "severity": "low",
                    "create_placeholder": False,
                },
            ],
        },
    )

    assert review_response.status_code == 200
    review = review_response.json()
    actions = review["actions_json"]
    assert len(actions) == 3
    assert actions[0]["created_placeholder_type"] == "control"
    assert actions[1]["created_placeholder_type"] == "evidence"
    assert "created_placeholder_type" not in actions[2]

    control = db_session.query(ComplianceControl).filter(
        ComplianceControl.id == actions[0]["control_id"],
    ).first()
    assert control is not None
    assert control.ai_system_id == system_id
    assert control.article == "Article 10"
    assert control.evidence_domain == "bias_testing"
    assert control.owner_email == "control.owner@example.com"

    evidence = db_session.query(EvidenceItem).filter(
        EvidenceItem.id == actions[1]["evidence_item_id"],
    ).first()
    assert evidence is not None
    assert evidence.ai_system_id == system_id
    assert evidence.evidence_type == "model_card"
    assert evidence.status == "needs_review"
    assert evidence.evidence_hash != "pending"

    tasks = db_session.query(ReviewTask).filter(
        ReviewTask.ai_system_id == system_id,
        ReviewTask.review_type == "ai_system_lifecycle_follow_up",
    ).all()
    assert len(tasks) == 3
    task_targets = {task.findings_json["target_type"] for task in tasks}
    assert task_targets == {"control", "evidence", "general"}

    workspace_response = client.get(f"/v1/ai-systems/{system_id}/workspace", headers=admin_headers)
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()
    assert workspace["metrics"]["follow_up_task_count"] == 3
    assert workspace["metrics"]["open_follow_up_task_count"] == 3
    assert workspace["metrics"]["linked_follow_up_task_count"] == 2
    assert workspace["metrics"]["control_count"] == 1
    assert workspace["metrics"]["evidence_item_count"] == 1


def test_ai_system_review_history_respects_tenant_isolation(client, admin_headers, db_session):
    db_session.add(Tenant(tenant_id="other-tenant", name="Other Tenant"))
    db_session.add(AiSystem(id="sys-other-review", tenant_id="other-tenant", name="Other Review"))
    db_session.commit()

    response = client.post(
        "/v1/ai-systems/sys-other-review/reviews",
        headers=admin_headers,
        json={"status": "completed"},
    )

    assert response.status_code == 404
