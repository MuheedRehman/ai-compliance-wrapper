import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config import DEFAULT_MODEL, FEATURE_ID_ENFORCEMENT, CANDIDATE_VERSION_POLICY
from app.services.ai_provider import call_ai_provider
from app.services.evidence_service import write_evidence_log, write_failure_evidence_independently
from app.services.feature_service import validate_registered_feature
from app.services.hashing import hash_object, sha256_text
from app.services.redaction import redact_metadata, redact_text
from app.services.review_service import get_or_create_open_review_task
from app.services.risk_engine import assess_risk
from app.services.billing_service import record_usage


@dataclass(kw_only=True)
class EventPayload:
    tenant_id: str
    feature_id: str
    request_id: str
    trace_id: str
    event_type: str
    decision: str
    status: str
    risk: dict
    policy_context: dict
    metadata: dict
    input_text: Optional[str]
    output_text: Optional[str]
    feature_pk: Optional[str] = None
    feature_version_id: Optional[str] = None
    policy_bundle_version: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    provider_response_id: Optional[str] = None
    finish_reason: Optional[str] = None
    request_hash: Optional[str] = None
    prompt_hash: Optional[str] = None
    response_hash: Optional[str] = None
    latency_ms: Optional[int] = None
    token_counts: Optional[dict] = None
    metadata_warnings: Optional[list] = None
    ai_system_id: Optional[str] = None
    evidence_domain: str = "runtime"


def normalize_messages(messages) -> list[dict]:
    return [message.model_dump() for message in messages]


def combine_all_message_text(messages: list[dict]) -> str:
    return "\n".join(f"{m.get('role', 'unknown')}: {m.get('content', '')}" for m in messages if isinstance(m.get("content", ""), str))


def governance_risk(rule_id: str, description: str, action: str = "block") -> dict:
    return {
        "risk_level": "high",
        "risk_score": 60,
        "rule_results": [{"rule_id": rule_id, "rule_group": "feature_governance", "severity": "high", "action": action, "description": description}],
        "triggered_rule_ids": [rule_id],
    }


def build_event_data(payload: EventPayload) -> dict:
    return {
        "event_type": payload.event_type,
        "tenant_id": payload.tenant_id,
        "ai_system_id": payload.ai_system_id,
        "evidence_domain": payload.evidence_domain,
        "feature_pk": payload.feature_pk,
        "feature_id": payload.feature_id,
        "feature_version_id": payload.feature_version_id,
        "policy_bundle_version": payload.policy_bundle_version,
        "request_id": payload.request_id,
        "trace_id": payload.trace_id,
        "provider": payload.provider,
        "model": payload.model,
        "provider_response_id": payload.provider_response_id,
        "finish_reason": payload.finish_reason,
        "decision": payload.decision,
        "status": payload.status,
        "risk_level": payload.risk.get("risk_level", "unknown"),
        "risk_score": payload.risk.get("risk_score", 0),
        "triggered_rule_results": payload.risk.get("rule_results", []),
        "request_hash": payload.request_hash,
        "prompt_hash": payload.prompt_hash,
        "response_hash": payload.response_hash,
        "latency_ms": payload.latency_ms,
        "token_counts": payload.token_counts or {},
        "metadata_warnings": payload.metadata_warnings or [],
        "policy_context": redact_metadata(payload.policy_context),
        "metadata": redact_metadata(payload.metadata),
        "redacted_input_text": redact_text(payload.input_text),
        "redacted_output_text": redact_text(payload.output_text),
    }


def write_event(db: Session, payload: EventPayload):
    return write_evidence_log(db, build_event_data(payload))


def run_chat_pipeline(db: Session, request, auth_context: dict) -> dict:
    try:
        result = _run_chat_pipeline_inner(db, request, auth_context)
        db.commit()
        return result
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


def _run_chat_pipeline_inner(db: Session, request, auth_context: dict) -> dict:
    start = time.time()
    tenant_id = auth_context["tenant_id"]
    request_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    provider = "openai"
    model = request.model or DEFAULT_MODEL
    messages = normalize_messages(request.messages)
    all_text = combine_all_message_text(messages)
    prompt_hash = sha256_text(all_text)
    feature_id = request.feature_id
    feature_pk = None
    feature_version_id = None
    policy_bundle_version = None
    ai_system_id = None
    metadata_warnings = []

    if not feature_id:
        metadata_warnings.append("missing_feature_id")
        feature_id = "unmapped_feature"
        get_or_create_open_review_task(db, tenant_id, feature_id, "feature_registration", "missing_feature_id", "medium", {"request_id": request_id, "trace_id": trace_id})

        request_hash = hash_object({"tenant_id": tenant_id, "feature_id": feature_id, "model": model, "messages": messages, "policy_context": request.policy_context})

        if FEATURE_ID_ENFORCEMENT == "block":
            risk = governance_risk("feature.missing_id_blocked", "Missing feature_id under block enforcement", "block")
            latency_ms = int((time.time() - start) * 1000)
            payload = EventPayload(
                tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
                event_type="request_blocked_missing_feature", decision="block", status="blocked",
                risk=risk, policy_context=request.policy_context, metadata=request.metadata,
                input_text=all_text, output_text=None, provider=provider, model=model,
                request_hash=request_hash, prompt_hash=prompt_hash, latency_ms=latency_ms,
                metadata_warnings=metadata_warnings
            )
            event = write_event(db, payload)
            return {"request_id": request_id, "trace_id": trace_id, "status": "blocked", "output": None, "message": "feature_id is required", "evidence": {"event_id": event.event_id, "event_hash": event.event_hash}}

        if FEATURE_ID_ENFORCEMENT == "quarantine":
            risk = governance_risk("feature.missing_id", "Missing feature_id under quarantine enforcement", "quarantine")
            latency_ms = int((time.time() - start) * 1000)
            payload = EventPayload(
                tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
                event_type="request_quarantined", decision="quarantine", status="quarantined",
                risk=risk, policy_context=request.policy_context, metadata=request.metadata,
                input_text=all_text, output_text=None, provider=provider, model=model,
                request_hash=request_hash, prompt_hash=prompt_hash, latency_ms=latency_ms,
                metadata_warnings=metadata_warnings
            )
            event = write_event(db, payload)
            return {"request_id": request_id, "trace_id": trace_id, "status": "quarantined", "output": None, "message": "Request quarantined because feature_id is missing.", "evidence": {"event_id": event.event_id, "event_hash": event.event_hash}}

    request_hash = hash_object({"tenant_id": tenant_id, "feature_id": feature_id, "model": model, "messages": messages, "policy_context": request.policy_context})
    pre_check = assess_risk(all_text, request.policy_context)

    if feature_id != "unmapped_feature":
        feature_result = validate_registered_feature(db, tenant_id, feature_id, provider, model, prompt_hash)

        if feature_result.get("feature"):
            feature_pk = feature_result["feature"].id
            ai_system_id = feature_result["feature"].ai_system_id

        if feature_result.get("allowed"):
            feature_version_id = feature_result.get("feature_version_id")
            policy_bundle_version = feature_result.get("policy_bundle_version")

            if feature_result.get("version_status") == "candidate":
                metadata_warnings.append("candidate_feature_version")
                get_or_create_open_review_task(db, tenant_id, feature_id, "change_triggered", "candidate_version_requires_review", "medium", {"request_id": request_id, "trace_id": trace_id, "candidate_policy": CANDIDATE_VERSION_POLICY}, feature_pk=feature_pk, feature_version_id=feature_version_id, ai_system_id=ai_system_id)

                if CANDIDATE_VERSION_POLICY in {"block", "quarantine"}:
                    action = CANDIDATE_VERSION_POLICY
                    risk = governance_risk(f"feature.candidate_version_{action}", "Candidate feature version is not approved", action)
                    latency_ms = int((time.time() - start) * 1000)
                    event_type = "request_blocked_candidate_version" if action == "block" else "request_quarantined_candidate_version"
                    payload = EventPayload(
                        tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
                        event_type=event_type, decision=action, status=f"{action}ed" if action == "quarantine" else "blocked",
                        risk=risk, policy_context=request.policy_context, metadata=request.metadata,
                        input_text=all_text, output_text=None, feature_pk=feature_pk,
                        feature_version_id=feature_version_id, policy_bundle_version=policy_bundle_version,
                        provider=provider, model=model, request_hash=request_hash, prompt_hash=prompt_hash,
                        latency_ms=latency_ms, metadata_warnings=metadata_warnings, ai_system_id=ai_system_id
                    )
                    event = write_event(db, payload)
                    return {"request_id": request_id, "trace_id": trace_id, "status": "quarantined" if action == "quarantine" else "blocked", "output": None, "message": "Candidate feature version is not approved.", "evidence": {"event_id": event.event_id, "event_hash": event.event_hash}}

        if not feature_result["allowed"]:
            get_or_create_open_review_task(db, tenant_id, feature_id, "feature_governance", feature_result["reason"], "high", {"message": feature_result["message"], "request_id": request_id, "trace_id": trace_id}, feature_pk=feature_pk, feature_version_id=feature_result.get("feature_version_id"), ai_system_id=ai_system_id)

            if FEATURE_ID_ENFORCEMENT == "warn" and feature_result["reason"] == "feature_not_registered":
                metadata_warnings.append("unknown_feature_allowed_in_warn_mode")
            else:
                risk = governance_risk(f"feature.{feature_result['reason']}", feature_result["message"], "block")
                latency_ms = int((time.time() - start) * 1000)
                payload = EventPayload(
                    tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
                    event_type="request_blocked_feature_policy", decision="block", status="blocked",
                    risk=risk, policy_context=request.policy_context, metadata=request.metadata,
                    input_text=all_text, output_text=None, feature_pk=feature_pk,
                    feature_version_id=feature_version_id, policy_bundle_version=policy_bundle_version,
                    provider=provider, model=model, request_hash=request_hash, prompt_hash=prompt_hash,
                    latency_ms=latency_ms, metadata_warnings=metadata_warnings, ai_system_id=ai_system_id
                )
                event = write_event(db, payload)
                return {"request_id": request_id, "trace_id": trace_id, "status": "blocked", "output": None, "message": feature_result["message"], "compliance": risk, "evidence": {"event_id": event.event_id, "event_hash": event.event_hash}}

    if pre_check["risk_level"] == "high":
        get_or_create_open_review_task(db, tenant_id, feature_id, "risk_review", "high_risk_pre_check", "high", {"request_id": request_id, "trace_id": trace_id, "rules": pre_check["triggered_rule_ids"]}, feature_pk=feature_pk, feature_version_id=feature_version_id, ai_system_id=ai_system_id)
        latency_ms = int((time.time() - start) * 1000)
        payload = EventPayload(
            tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
            event_type="request_blocked_pre_check", decision="block", status="blocked",
            risk=pre_check, policy_context=request.policy_context, metadata=request.metadata,
            input_text=all_text, output_text=None, feature_pk=feature_pk,
            feature_version_id=feature_version_id, policy_bundle_version=policy_bundle_version,
            provider=provider, model=model, request_hash=request_hash, prompt_hash=prompt_hash,
            latency_ms=latency_ms, metadata_warnings=metadata_warnings, ai_system_id=ai_system_id
        )
        event = write_event(db, payload)
        return {"request_id": request_id, "trace_id": trace_id, "status": "blocked", "output": None, "compliance": pre_check, "evidence": {"event_id": event.event_id, "event_hash": event.event_hash}}

    try:
        ai_result = call_ai_provider(provider, messages, model, request.max_tokens)
        output_text = ai_result["output_text"]
    except Exception as exc:
        latency_ms = int((time.time() - start) * 1000)
        payload = EventPayload(
            tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
            event_type="provider_error", decision="error", status="error",
            risk=pre_check, policy_context=request.policy_context, metadata=request.metadata,
            input_text=all_text, output_text=str(exc), feature_pk=feature_pk,
            feature_version_id=feature_version_id, policy_bundle_version=policy_bundle_version,
            provider=provider, model=model, request_hash=request_hash, prompt_hash=prompt_hash,
            latency_ms=latency_ms, metadata_warnings=metadata_warnings, ai_system_id=ai_system_id
        )
        event_data = build_event_data(payload)

        # Provider-error evidence is intentionally written outside the main
        # request transaction so it survives rollback.
        #
        # SQLite allows only one writer at a time. In local tests, the main
        # request session may already have flushed auth/feature state before
        # the provider fails. Roll it back first so the independent evidence
        # writer can acquire the SQLite write lock.
        #
        # In Postgres this also keeps the semantic clean: provider failure
        # evidence survives, while partial request state is discarded.
        db.rollback()

        event = write_failure_evidence_independently(event_data)
        raise HTTPException(
            status_code=502,
            detail={
                "message": "AI provider request failed",
                "event_id": event.event_id,
            },
        )

    post_check = assess_risk(output_text, request.policy_context)
    final_score = max(pre_check["risk_score"], post_check["risk_score"])
    rule_results = pre_check.get("rule_results", []) + post_check.get("rule_results", [])
    if final_score >= 60:
        final_level = "high"
        decision = "flag"
    elif final_score >= 25:
        final_level = "medium"
        decision = "allow_with_warning"
    elif "candidate_feature_version" in metadata_warnings:
        final_level = "low"
        decision = "allow_with_warning"
    else:
        final_level = "low"
        decision = "allow"

    final_risk = {
        "risk_level": final_level,
        "risk_score": final_score,
        "rule_results": rule_results,
        "triggered_rule_ids": sorted({r["rule_id"] for r in rule_results}),
    }

    response_hash = sha256_text(output_text)
    latency_ms = int((time.time() - start) * 1000)
    payload = EventPayload(
        tenant_id=tenant_id, feature_id=feature_id, request_id=request_id, trace_id=trace_id,
        event_type="ai_request_completed", decision=decision, status="completed",
        risk=final_risk, policy_context=request.policy_context, metadata=request.metadata,
        input_text=all_text, output_text=output_text, feature_pk=feature_pk,
        feature_version_id=feature_version_id, policy_bundle_version=policy_bundle_version,
        provider=provider, model=ai_result["model"], provider_response_id=ai_result.get("provider_response_id"),
        finish_reason=ai_result.get("finish_reason"), request_hash=request_hash, prompt_hash=prompt_hash,
        response_hash=response_hash, latency_ms=latency_ms, token_counts=ai_result.get("usage", {}),
        metadata_warnings=metadata_warnings, ai_system_id=ai_system_id
    )
    event = write_event(db, payload)

    record_usage(db, tenant_id, "governed_call", 1)

    return {"request_id": request_id, "trace_id": trace_id, "status": "completed", "output": output_text, "compliance": {"risk_level": final_level, "risk_score": final_score, "decision": decision, "triggered_rule_ids": final_risk["triggered_rule_ids"], "rule_results": rule_results}, "evidence": {"event_id": event.event_id, "event_hash": event.event_hash, "hmac_signature": event.hmac_signature, "feature_version_id": feature_version_id, "policy_bundle_version": policy_bundle_version, "metadata_warnings": metadata_warnings}}
