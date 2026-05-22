from datetime import datetime, timedelta, timezone

from app.models import AiSystem, ComplianceControl, EvidenceArtifact, EvidenceItem, Tenant


def _create_system_and_control(client, admin_headers):
    system_response = client.post(
        "/v1/ai-systems",
        headers=admin_headers,
        json={"name": "Evidence Vault System", "description": "System for vault tests"},
    )
    assert system_response.status_code == 200
    system_id = system_response.json()["id"]

    control_response = client.post(
        "/v1/compliance/controls",
        headers=admin_headers,
        json={
            "ai_system_id": system_id,
            "control_key": "EV_TEST_CONTROL",
            "article": "Article 12",
            "title": "Logging evidence retained",
            "evidence_domain": "log_retention",
        },
    )
    assert control_response.status_code == 200
    return system_response.json(), control_response.json()


def test_evidence_vault_create_filter_update_summary_and_workspace(client, admin_headers):
    system, control = _create_system_and_control(client, admin_headers)
    review_at = datetime.now(timezone.utc) - timedelta(days=1)
    expires_at = datetime.now(timezone.utc) + timedelta(days=10)

    create_response = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "SOC 2 controls excerpt",
            "evidence_type": "vendor_doc",
            "source": "Vendor trust center",
            "source_url": "https://example.com/security",
            "owner_email": "audit@example.com",
            "ai_system_id": system["id"],
            "control_id": control["id"],
            "review_at": review_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "metadata_json": {"document_version": "2026.05"},
        },
    )
    assert create_response.status_code == 200
    item = create_response.json()
    assert item["ai_system_id"] == system["id"]
    assert item["control_id"] == control["id"]
    assert item["status"] == "active"
    assert len(item["evidence_hash"]) == 64
    assert len(item["hmac_signature"]) == 64

    list_response = client.get(
        f"/v1/evidence/items?ai_system_id={system['id']}&evidence_type=vendor_doc",
        headers=admin_headers,
    )
    assert list_response.status_code == 200
    assert [record["id"] for record in list_response.json()] == [item["id"]]

    summary_response = client.get(f"/v1/evidence/summary?ai_system_id={system['id']}", headers=admin_headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_items"] == 1
    assert summary["due_for_review_count"] == 1
    assert summary["expiring_soon_count"] == 1
    assert summary["items_by_type"]["vendor_doc"] == 1

    update_response = client.patch(
        f"/v1/evidence/items/{item['id']}",
        headers=admin_headers,
        json={"status": "needs_review", "owner_email": "reviewer@example.com"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "needs_review"
    assert updated["owner_email"] == "reviewer@example.com"
    assert updated["evidence_hash"] != item["evidence_hash"]

    workspace_response = client.get(f"/v1/ai-systems/{system['id']}/workspace", headers=admin_headers)
    assert workspace_response.status_code == 200
    workspace = workspace_response.json()
    assert workspace["metrics"]["evidence_item_count"] == 1
    assert workspace["evidence_items"][0]["id"] == item["id"]


def test_evidence_vault_rejects_foreign_control(client, admin_headers, db_session):
    db_session.add(Tenant(tenant_id="tenant-other", name="Other Tenant"))
    db_session.add(AiSystem(id="sys-other-evidence", tenant_id="tenant-other", name="Other System"))
    db_session.add(ComplianceControl(
        id="ctrl-other-evidence",
        tenant_id="tenant-other",
        ai_system_id="sys-other-evidence",
        control_key="OTHER",
        article="Article 10",
        title="Other tenant control",
        evidence_domain="classification",
    ))
    db_session.commit()

    response = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "Foreign control evidence",
            "evidence_type": "policy",
            "source": "Internal drive",
            "control_id": "ctrl-other-evidence",
        },
    )
    assert response.status_code == 404


def test_evidence_vault_requires_evidence_scope(client, app_headers):
    response = client.get("/v1/evidence/items", headers=app_headers)
    assert response.status_code == 403


def test_evidence_item_model_persists_signature(db_session, client, admin_headers):
    system, _ = _create_system_and_control(client, admin_headers)
    response = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "Human oversight checklist",
            "evidence_type": "human_oversight",
            "source": "Governance workspace",
            "ai_system_id": system["id"],
        },
    )
    assert response.status_code == 200
    item_id = response.json()["id"]

    stored = db_session.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    assert stored is not None
    assert stored.hmac_signature == response.json()["hmac_signature"]


def test_evidence_vault_uploads_signed_artifact_and_downloads_content(client, admin_headers, db_session):
    system, control = _create_system_and_control(client, admin_headers)
    create_response = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "Model card upload",
            "evidence_type": "model_card",
            "source": "Evidence Vault upload",
            "ai_system_id": system["id"],
            "control_id": control["id"],
        },
    )
    assert create_response.status_code == 200
    item = create_response.json()
    original_hash = item["evidence_hash"]

    upload_response = client.post(
        f"/v1/evidence/items/{item['id']}/artifacts",
        headers=admin_headers,
        files={"file": ("model-card.txt", b"model card evidence", "text/plain")},
    )
    assert upload_response.status_code == 200
    artifact = upload_response.json()
    assert artifact["file_name"] == "model-card.txt"
    assert artifact["content_type"] == "text/plain"
    assert artifact["size_bytes"] == len(b"model card evidence")
    assert len(artifact["artifact_hash"]) == 64
    assert len(artifact["hmac_signature"]) == 64
    assert artifact["storage_backend"] == "database"

    stored_artifact = db_session.query(EvidenceArtifact).filter(EvidenceArtifact.id == artifact["id"]).first()
    assert stored_artifact is not None
    assert stored_artifact.content_bytes == b"model card evidence"

    list_response = client.get(f"/v1/evidence/items?ai_system_id={system['id']}", headers=admin_headers)
    assert list_response.status_code == 200
    uploaded_item = list_response.json()[0]
    assert uploaded_item["id"] == item["id"]
    assert uploaded_item["evidence_hash"] != original_hash
    assert uploaded_item["metadata_json"]["artifact_count"] == 1
    assert uploaded_item["artifacts"][0]["id"] == artifact["id"]

    download_response = client.get(
        f"/v1/evidence/items/{item['id']}/artifacts/{artifact['id']}/download",
        headers=admin_headers,
    )
    assert download_response.status_code == 200
    assert download_response.content == b"model card evidence"
    assert download_response.headers["x-evidence-artifact-hash"] == artifact["artifact_hash"]

    preview_response = client.get(
        f"/v1/evidence/items/{item['id']}/artifacts/{artifact['id']}/preview",
        headers=admin_headers,
    )
    assert preview_response.status_code == 200
    assert preview_response.content == b"model card evidence"
    assert preview_response.headers["content-disposition"].startswith("inline;")
    assert preview_response.headers["x-content-type-options"] == "nosniff"
    assert preview_response.headers["x-evidence-artifact-hash"] == artifact["artifact_hash"]


def test_evidence_vault_preview_rejects_unsupported_artifact_type(client, admin_headers):
    system, control = _create_system_and_control(client, admin_headers)
    create_response = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "Archive upload",
            "evidence_type": "other",
            "source": "Evidence Vault upload",
            "ai_system_id": system["id"],
            "control_id": control["id"],
        },
    )
    assert create_response.status_code == 200
    item = create_response.json()

    upload_response = client.post(
        f"/v1/evidence/items/{item['id']}/artifacts",
        headers=admin_headers,
        files={"file": ("archive.zip", b"PK\x03\x04 archive bytes", "application/zip")},
    )
    assert upload_response.status_code == 200
    artifact = upload_response.json()

    preview_response = client.get(
        f"/v1/evidence/items/{item['id']}/artifacts/{artifact['id']}/preview",
        headers=admin_headers,
    )
    assert preview_response.status_code == 415
