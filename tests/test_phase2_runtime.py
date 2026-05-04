import uuid
import pytest
from app.models import AiSystem, AiFeature, EvidenceLog, ReviewTask

def test_evidence_includes_ai_system_id_and_runtime_domain(client, app_headers, chat_payload, fake_provider, db_session):
    # 1. Create an AiSystem
    system_id = str(uuid.uuid4())
    system = AiSystem(id=system_id, tenant_id="tenant_test", name="Linked System")
    db_session.add(system)
    
    # 2. Link the feature to the system
    feature = db_session.query(AiFeature).filter_by(feature_id="customer_support_bot").first()
    feature.ai_system_id = system_id
    db_session.commit()
    
    # 3. Run pipeline
    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)
    assert response.status_code == 200
    
    # 4. Verify evidence
    evidence = db_session.query(EvidenceLog).filter_by(feature_id="customer_support_bot").first()
    assert evidence.ai_system_id == system_id
    assert evidence.evidence_domain == "runtime"

def test_evidence_includes_runtime_domain_for_unlinked_features(client, chat_payload, fake_provider, db_session):
    # Unlinked feature test
    response = client.post("/v1/chat/completions", headers={"x-api-key": "aigw_test_app_key_123"}, json=chat_payload)
    assert response.status_code == 200
    
    evidence = db_session.query(EvidenceLog).first()
    assert evidence is not None
    assert evidence.ai_system_id is None
    assert evidence.evidence_domain == "runtime"

def test_logs_filtering_by_domain_and_system(client, app_headers, db_session):
    # Create two logs with different domains and systems
    system_id = str(uuid.uuid4())
    
    # Log 1: runtime domain, linked
    log1 = EvidenceLog(
        event_id=str(uuid.uuid4()), tenant_id="tenant_test", request_id="req1", trace_id="tr1",
        event_type="test", decision="allow", status="completed", risk_level="low", risk_score=0,
        event_hash="h1", hmac_signature="s1", token_counts={}, metadata_warnings=[],
        policy_context={}, metadata={}, evidence_json={},
        evidence_domain="runtime", ai_system_id=system_id
    )
    # Log 2: incident domain, unlinked
    log2 = EvidenceLog(
        event_id=str(uuid.uuid4()), tenant_id="tenant_test", request_id="req2", trace_id="tr2",
        event_type="test", decision="allow", status="completed", risk_level="low", risk_score=0,
        event_hash="h2", hmac_signature="s2", token_counts={}, metadata_warnings=[],
        policy_context={}, metadata={}, evidence_json={},
        evidence_domain="incident", ai_system_id=None
    )
    db_session.add_all([log1, log2])
    db_session.commit()
    
    # Filter by domain=runtime
    resp = client.get("/v1/logs?evidence_domain=runtime", headers=app_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    logs = resp.json()["logs"]
    assert len(logs) == 1, f"Expected 1 log, got {len(logs)}. Response: {resp.json()}"
    # Use .get() or check keys to avoid KeyError during debug
    assert "event_id" in logs[0], f"event_id missing in response log. Keys: {list(logs[0].keys())}"
    assert logs[0]["event_id"] == log1.event_id
    
    # Filter by ai_system_id
    resp = client.get(f"/v1/logs?ai_system_id={system_id}", headers=app_headers)
    assert resp.status_code == 200
    assert len(resp.json()["logs"]) == 1
    assert "event_id" in resp.json()["logs"][0]
    assert resp.json()["logs"][0]["event_id"] == log1.event_id

def test_reviews_filtering_by_system(client, admin_headers, db_session):
    system_id = str(uuid.uuid4())
    
    # Task 1: Linked
    task1 = ReviewTask(
        review_task_id=str(uuid.uuid4()), tenant_id="tenant_test", feature_id="f1",
        review_type="risk_review", trigger_reason="test", findings_json={},
        ai_system_id=system_id
    )
    # Task 2: Unlinked
    task2 = ReviewTask(
        review_task_id=str(uuid.uuid4()), tenant_id="tenant_test", feature_id="f2",
        review_type="risk_review", trigger_reason="test", findings_json={},
        ai_system_id=None
    )
    db_session.add_all([task1, task2])
    db_session.commit()
    
    # Filter by ai_system_id
    resp = client.get(f"/v1/review-tasks?ai_system_id={system_id}", headers=admin_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    tasks = resp.json()["review_tasks"]
    assert len(tasks) == 1, f"Expected 1 task, got {len(tasks)}. Response: {resp.json()}"
    assert "review_task_id" in tasks[0], f"review_task_id missing in response task. Keys: {list(tasks[0].keys())}"
    assert tasks[0]["review_task_id"] == task1.review_task_id
    
    # No filter shows both (backward compatibility)
    resp = client.get("/v1/review-tasks", headers=admin_headers)
    assert resp.status_code == 200
    # Filter by tenant_id is implicit in route, so we expect at least these 2
    task_ids = [t.get("review_task_id") for t in resp.json()["review_tasks"]]
    assert task1.review_task_id in task_ids
    assert task2.review_task_id in task_ids

def test_features_serialization_check(client, app_headers, db_session):
    resp = client.get("/v1/features", headers=app_headers)
    assert resp.status_code == 200
    features = resp.json()["features"]
    assert len(features) > 0
    # Check if a known field is present
    assert "feature_id" in features[0], f"feature_id missing. Keys: {list(features[0].keys())}"

def test_review_task_backfill(db_session):
    from app.services.review_service import get_or_create_open_review_task
    feature_id = "test_backfill_feature"
    tenant_id = "tenant_test"
    
    # Create an open legacy task with ai_system_id = None
    task_id = str(uuid.uuid4())
    task = ReviewTask(
        review_task_id=task_id,
        tenant_id=tenant_id,
        feature_id=feature_id,
        review_type="risk_review",
        trigger_reason="high_risk",
        status="open",
        occurrence_count=1,
        findings_json={}
    )
    db_session.add(task)
    db_session.commit()
    
    # Trigger the same review path with a linked feature
    system_id = str(uuid.uuid4())
    updated_task = get_or_create_open_review_task(
        db_session,
        tenant_id=tenant_id,
        feature_id=feature_id,
        review_type="risk_review",
        trigger_reason="high_risk",
        severity="high",
        findings={"test": "data"},
        ai_system_id=system_id
    )
    db_session.commit()
    
    assert updated_task.review_task_id == task_id
    assert updated_task.occurrence_count == 2
    assert updated_task.ai_system_id == system_id


