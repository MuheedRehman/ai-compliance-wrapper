"""Runtime policy check service.

Evaluates a prompt against per-feature governance rules and logs the decision.
Never stores the raw prompt — only a SHA-256 hash for auditability.
"""
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import AiFeature, FRIARecord, RuntimePolicyCheck


# ---- Rule definitions -------------------------------------------------------

_MAX_PROMPT_LENGTH = 16_000  # chars

_BLOCKED_PATTERNS = [
    ("jailbreak_attempt", ["ignore previous instructions", "ignore all instructions",
                           "disregard your instructions", "override your instructions",
                           "forget your system prompt"]),
    ("pii_exfiltration", ["social security number", "ssn:", "credit card number",
                          "passport number", "date of birth"]),
]


# ---- Internal helpers -------------------------------------------------------

def _hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()


def _check_content(prompt: str) -> list[dict]:
    lower = prompt.lower()
    violations = []
    for rule_id, patterns in _BLOCKED_PATTERNS:
        for p in patterns:
            if p in lower:
                violations.append({"rule_id": rule_id, "pattern": p})
                break
    if len(prompt) > _MAX_PROMPT_LENGTH:
        violations.append({"rule_id": "prompt_too_long", "max": _MAX_PROMPT_LENGTH, "actual": len(prompt)})
    return violations


# ---- Public API -------------------------------------------------------------

def run_policy_check(
    db: Session,
    *,
    tenant_id: str,
    api_key_id: Optional[str],
    prompt: str,
    feature_id: Optional[str],
    context: Optional[dict],
) -> dict:
    t0 = time.monotonic()
    check_id = f"chk-{uuid.uuid4().hex[:10]}"
    decision = "allow"
    reason = "All checks passed."
    policy_refs: list[str] = []
    feature_name: Optional[str] = None
    ai_system_id: Optional[str] = None
    risk_level: Optional[str] = None

    # 1 — Content policy
    violations = _check_content(prompt)
    if violations:
        decision = "block"
        rule_ids = [v["rule_id"] for v in violations]
        reason = f"Content policy violation: {', '.join(rule_ids)}."
        policy_refs.extend(rule_ids)

    # 2 — Feature gate (only when a feature_id is supplied)
    if feature_id and decision == "allow":
        feature = db.query(AiFeature).filter(
            AiFeature.tenant_id == tenant_id,
            (AiFeature.feature_id == feature_id) | (AiFeature.id == feature_id),
        ).first()

        if not feature:
            decision = "block"
            reason = f"Feature '{feature_id}' is not registered in this tenant."
            policy_refs.append("unknown_feature")
        else:
            feature_name = feature.name
            ai_system_id = feature.ai_system_id
            risk_level = feature.risk_level_current

            if feature.compliance_status not in ("active", "approved", None):
                decision = "block"
                reason = f"Feature '{feature.name}' is not in an active compliance state ({feature.compliance_status})."
                policy_refs.append("feature_not_active")

            if decision == "allow" and feature.risk_level_current == "high":
                fria = db.query(FRIARecord).filter(
                    FRIARecord.tenant_id == tenant_id,
                    FRIARecord.ai_system_id == feature.ai_system_id,
                    FRIARecord.status.in_(["approved", "completed"]),
                ).first() if feature.ai_system_id else None

                if not fria:
                    decision = "review"
                    reason = "High-risk feature requires a completed FRIA before unrestricted use."
                    policy_refs.append("fria_required")

    latency_ms = int((time.monotonic() - t0) * 1000)

    # Persist log record
    record = RuntimePolicyCheck(
        id=check_id,
        tenant_id=tenant_id,
        api_key_id=api_key_id,
        feature_id=feature_id,
        ai_system_id=ai_system_id,
        prompt_hash=_hash_prompt(prompt),
        prompt_length=len(prompt),
        decision=decision,
        reason=reason,
        policy_refs=policy_refs,
        latency_ms=latency_ms,
    )
    db.add(record)
    db.commit()

    return {
        "check_id": check_id,
        "decision": decision,
        "reason": reason,
        "feature_id": feature_id,
        "feature_name": feature_name,
        "ai_system_id": ai_system_id,
        "risk_level": risk_level,
        "policy_refs": policy_refs,
        "latency_ms": latency_ms,
    }


def get_usage_stats(db: Session, tenant_id: str, period_days: int = 7) -> dict:
    from sqlalchemy import func, case
    from datetime import timedelta

    since = datetime.now(timezone.utc) - timedelta(days=period_days)
    rows = db.query(RuntimePolicyCheck).filter(
        RuntimePolicyCheck.tenant_id == tenant_id,
        RuntimePolicyCheck.created_at >= since,
    ).all()

    total = len(rows)
    allow_count = sum(1 for r in rows if r.decision == "allow")
    block_count = sum(1 for r in rows if r.decision == "block")
    review_count = sum(1 for r in rows if r.decision == "review")

    # Top features by check count
    feature_counts: dict[str, int] = {}
    for r in rows:
        if r.feature_id:
            feature_counts[r.feature_id] = feature_counts.get(r.feature_id, 0) + 1
    top_features = [
        {"feature_id": fid, "check_count": cnt}
        for fid, cnt in sorted(feature_counts.items(), key=lambda x: -x[1])[:10]
    ]

    # Daily breakdown
    daily_map: dict[str, dict] = {}
    for r in rows:
        day = r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown"
        if day not in daily_map:
            daily_map[day] = {"date": day, "total": 0, "allow": 0, "block": 0, "review": 0}
        daily_map[day]["total"] += 1
        daily_map[day][r.decision] = daily_map[day].get(r.decision, 0) + 1

    daily = sorted(daily_map.values(), key=lambda x: x["date"])

    return {
        "tenant_id": tenant_id,
        "period_days": period_days,
        "total_checks": total,
        "allow_count": allow_count,
        "block_count": block_count,
        "review_count": review_count,
        "top_features": top_features,
        "daily": daily,
    }
