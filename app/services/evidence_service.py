import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import EvidenceLog
from app.services.hashing import hash_object, hmac_signature


def get_last_event_hash(db: Session, tenant_id: str) -> str | None:
    last = db.query(EvidenceLog).filter(EvidenceLog.tenant_id == tenant_id).order_by(EvidenceLog.created_at.desc(), EvidenceLog.event_id.desc()).first()
    return last.event_hash if last else None


def write_evidence_log(db: Session, event_data: dict) -> EvidenceLog:
    previous_event_hash = get_last_event_hash(db, event_data["tenant_id"])

    base_event = {"event_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(), "previous_event_hash": previous_event_hash, **event_data}
    event_hash = hash_object(base_event)
    signature = hmac_signature({"event_hash": event_hash, "previous_event_hash": previous_event_hash, "event_id": base_event["event_id"], "timestamp": base_event["timestamp"]})

    evidence = EvidenceLog(
        event_id=base_event["event_id"],
        tenant_id=event_data["tenant_id"],
        feature_pk=event_data.get("feature_pk"),
        feature_id=event_data.get("feature_id"),
        feature_version_id=event_data.get("feature_version_id"),
        policy_bundle_version=event_data.get("policy_bundle_version"),
        request_id=event_data["request_id"],
        trace_id=event_data["trace_id"],
        event_type=event_data["event_type"],
        provider=event_data.get("provider"),
        model=event_data.get("model"),
        provider_response_id=event_data.get("provider_response_id"),
        finish_reason=event_data.get("finish_reason"),
        decision=event_data["decision"],
        status=event_data["status"],
        risk_level=event_data["risk_level"],
        risk_score=event_data["risk_score"],
        triggered_rule_results=event_data.get("triggered_rule_results", []),
        request_hash=event_data.get("request_hash"),
        prompt_hash=event_data.get("prompt_hash"),
        response_hash=event_data.get("response_hash"),
        previous_event_hash=previous_event_hash,
        event_hash=event_hash,
        hmac_signature=signature,
        latency_ms=event_data.get("latency_ms"),
        token_counts=event_data.get("token_counts", {}),
        metadata_warnings=event_data.get("metadata_warnings", []),
        policy_context=event_data.get("policy_context", {}),
        request_metadata=event_data.get("metadata", {}),
        redacted_input_text=event_data.get("redacted_input_text"),
        redacted_output_text=event_data.get("redacted_output_text"),
        evidence_json=base_event,
    )
    db.add(evidence)
    db.flush()
    return evidence


def write_failure_evidence_independently(event_data: dict) -> EvidenceLog:
    db = SessionLocal()
    try:
        evidence = write_evidence_log(db, event_data)
        db.commit()
        db.refresh(evidence)
        return evidence
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
