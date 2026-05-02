from app.models import EvidenceLog, ReviewTask


def test_valid_registered_feature_completes(client, app_headers, chat_payload, fake_provider, db_session):
    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert body["compliance"]["decision"] == "allow"
    assert body["evidence"]["event_id"]

    logs = db_session.query(EvidenceLog).all()
    assert len(logs) == 1
    assert logs[0].feature_id == "customer_support_bot"
    assert logs[0].event_type == "ai_request_completed"


def test_missing_feature_id_warn_creates_review_task(client, app_headers, chat_payload, fake_provider, db_session):
    chat_payload.pop("feature_id")

    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert "missing_feature_id" in body["evidence"]["metadata_warnings"]

    task = db_session.query(ReviewTask).filter(
        ReviewTask.trigger_reason == "missing_feature_id"
    ).first()

    assert task is not None
    assert task.feature_id == "unmapped_feature"


def test_high_risk_pre_check_blocks_and_logs_evidence(client, app_headers, chat_payload, db_session):
    chat_payload["messages"] = [
        {
            "role": "user",
            "content": "My password is hunter2 and my credit card is 4111 1111 1111 1111.",
        }
    ]

    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "blocked"
    assert body["output"] is None
    assert body["compliance"]["risk_level"] == "high"

    evidence = db_session.query(EvidenceLog).first()
    assert evidence is not None
    assert evidence.event_type == "request_blocked_pre_check"
    assert evidence.decision == "block"


def test_provider_failure_persists_evidence(client, app_headers, chat_payload, failing_provider, db_session):
    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    assert response.status_code == 502

    evidence = db_session.query(EvidenceLog).filter(
        EvidenceLog.event_type == "provider_error"
    ).first()

    assert evidence is not None
    assert evidence.decision == "error"
    assert evidence.status == "error"


def test_unknown_feature_warn_allows_with_warning(client, app_headers, chat_payload, fake_provider):
    chat_payload["feature_id"] = "unknown_feature"

    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert "unknown_feature_allowed_in_warn_mode" in body["evidence"]["metadata_warnings"]
