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
