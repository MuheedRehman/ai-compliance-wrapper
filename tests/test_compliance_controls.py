from fastapi.testclient import TestClient

from app.models import AiSystem


def test_seed_baseline_controls_and_scorecard(client: TestClient, admin_headers, db_session):
    system = AiSystem(id="sys-controls", tenant_id="tenant_test", name="Controls System")
    db_session.add(system)
    db_session.commit()

    res = client.post("/v1/compliance/controls/seed-baseline?ai_system_id=sys-controls", headers=admin_headers)
    assert res.status_code == 200
    controls = res.json()
    assert len(controls) >= 6
    assert any(c["control_key"] == "ai_literacy_program" for c in controls)
    assert any(c["article"] == "Article 73" for c in controls)

    first_id = controls[0]["id"]
    res = client.patch(
        f"/v1/compliance/controls/{first_id}",
        json={"status": "completed", "owner_email": "owner@example.com"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"

    res = client.get("/v1/compliance/scorecard?ai_system_id=sys-controls", headers=admin_headers)
    assert res.status_code == 200
    scorecard = res.json()
    assert scorecard["total_controls"] == len(controls)
    assert scorecard["completed_controls"] == 1
    assert scorecard["readiness_score"] > 0


def test_control_rejects_foreign_system(client: TestClient, admin_headers, db_session):
    from app.models import Tenant

    db_session.add(Tenant(tenant_id="other-tenant", name="Other"))
    db_session.add(AiSystem(id="other-system", tenant_id="other-tenant", name="Other System"))
    db_session.commit()

    payload = {
        "ai_system_id": "other-system",
        "control_key": "ai_literacy_program",
        "article": "Article 4",
        "title": "AI literacy",
        "evidence_domain": "ai_literacy",
    }
    res = client.post("/v1/compliance/controls", json=payload, headers=admin_headers)
    assert res.status_code == 404


def test_control_evidence_attachment_workflow(client: TestClient, admin_headers):
    system_response = client.post(
        "/v1/ai-systems",
        headers=admin_headers,
        json={"name": "Control Evidence System"},
    )
    assert system_response.status_code == 200
    system_id = system_response.json()["id"]

    control_response = client.post(
        "/v1/compliance/controls",
        headers=admin_headers,
        json={
            "ai_system_id": system_id,
            "control_key": "CONTROL_EVIDENCE_LINK",
            "article": "Article 12",
            "title": "Logging evidence attached",
            "evidence_domain": "log_retention",
        },
    )
    assert control_response.status_code == 200
    control = control_response.json()
    assert control["evidence_item_count"] == 0

    evidence_response = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "Log retention policy",
            "evidence_type": "policy",
            "source": "Internal policy drive",
        },
    )
    assert evidence_response.status_code == 200
    evidence = evidence_response.json()

    attach_response = client.post(
        f"/v1/compliance/controls/{control['id']}/evidence/{evidence['id']}",
        headers=admin_headers,
    )
    assert attach_response.status_code == 200
    attached = attach_response.json()
    assert attached["control_id"] == control["id"]
    assert attached["ai_system_id"] == system_id
    assert attached["evidence_hash"] != evidence["evidence_hash"]
    assert attached["metadata_json"]["latest_control_attachment"]["control_id"] == control["id"]

    evidence_list_response = client.get(
        f"/v1/compliance/controls/{control['id']}/evidence",
        headers=admin_headers,
    )
    assert evidence_list_response.status_code == 200
    assert [item["id"] for item in evidence_list_response.json()] == [evidence["id"]]

    controls_response = client.get(f"/v1/compliance/controls?ai_system_id={system_id}", headers=admin_headers)
    assert controls_response.status_code == 200
    refreshed = controls_response.json()[0]
    assert refreshed["evidence_item_count"] == 1
    assert refreshed["active_evidence_count"] == 1
    assert refreshed["evidence_status_counts"]["active"] == 1


def test_control_evidence_attachment_rejects_different_system(client: TestClient, admin_headers):
    first_system = client.post("/v1/ai-systems", headers=admin_headers, json={"name": "Control System A"}).json()
    second_system = client.post("/v1/ai-systems", headers=admin_headers, json={"name": "Control System B"}).json()

    control = client.post(
        "/v1/compliance/controls",
        headers=admin_headers,
        json={
            "ai_system_id": first_system["id"],
            "control_key": "CONTROL_SYSTEM_A",
            "article": "Article 14",
            "title": "Human oversight control",
            "evidence_domain": "human_oversight",
        },
    ).json()
    evidence = client.post(
        "/v1/evidence/items",
        headers=admin_headers,
        json={
            "title": "Wrong system evidence",
            "evidence_type": "policy",
            "source": "Internal drive",
            "ai_system_id": second_system["id"],
        },
    ).json()

    response = client.post(
        f"/v1/compliance/controls/{control['id']}/evidence/{evidence['id']}",
        headers=admin_headers,
    )
    assert response.status_code == 400
