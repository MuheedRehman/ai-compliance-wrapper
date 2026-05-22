import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AiSystem, ComplianceControl, EvidenceItem
from app.schemas import (
    ComplianceControlCreate,
    ComplianceControlReviewCreate,
    ComplianceControlTemplateApplyRequest,
    ComplianceControlUpdate,
)


BASELINE_CONTROLS = [
    {
        "control_key": "ai_literacy_program",
        "article": "Article 4",
        "title": "AI literacy program and training evidence",
        "evidence_domain": "ai_literacy",
    },
    {
        "control_key": "deployer_log_retention",
        "article": "Article 26(6)",
        "title": "High-risk deployer log retention of at least six months",
        "evidence_domain": "log_retention",
    },
    {
        "control_key": "dpia_linkage",
        "article": "Article 26(9)",
        "title": "DPIA linkage and privacy assessment evidence",
        "evidence_domain": "privacy_dpia",
    },
    {
        "control_key": "fria_screening",
        "article": "Article 27",
        "title": "FRIA applicability screening and assessment record",
        "evidence_domain": "governance_fria",
    },
    {
        "control_key": "post_market_monitoring",
        "article": "Article 72",
        "title": "Post-market monitoring plan and review cadence",
        "evidence_domain": "post_market_monitoring",
    },
    {
        "control_key": "serious_incident_reporting",
        "article": "Article 73",
        "title": "Serious incident reporting deadlines and authority notification",
        "evidence_domain": "governance_incident",
    },
]

BASELINE_LIFECYCLE = {
    "ai_literacy_program": {"severity": "medium", "review_cycle_days": 365},
    "deployer_log_retention": {"severity": "high", "review_cycle_days": 180},
    "dpia_linkage": {"severity": "high", "review_cycle_days": 365},
    "fria_screening": {"severity": "high", "review_cycle_days": 180},
    "post_market_monitoring": {"severity": "high", "review_cycle_days": 90},
    "serious_incident_reporting": {"severity": "critical", "review_cycle_days": 90},
}

CONTROL_TEMPLATES = [
    {
        "template_key": "human_oversight_implemented",
        "article": "Article 14",
        "title": "Human oversight implemented and assigned",
        "evidence_domain": "human_oversight",
        "default_severity": "high",
        "default_review_cycle_days": 180,
        "description": "Confirm trained human reviewers can monitor, interpret, override, or stop the AI system where required.",
        "suggested_evidence": ["Oversight procedure", "Reviewer assignment", "Escalation runbook"],
        "actor_roles": ["provider", "deployer"],
        "risk_tiers": ["high_risk"],
    },
    {
        "template_key": "logging_monitoring_enabled",
        "article": "Article 12",
        "title": "Logging and monitoring enabled",
        "evidence_domain": "log_retention",
        "default_severity": "high",
        "default_review_cycle_days": 180,
        "description": "Verify logs are captured, retained, monitored, and available for traceability and post-market review.",
        "suggested_evidence": ["Log retention policy", "Monitoring dashboard", "Sample audit log"],
        "actor_roles": ["provider", "deployer"],
        "risk_tiers": ["high_risk", "transparency"],
    },
    {
        "template_key": "user_disclosure_present",
        "article": "Article 50",
        "title": "User-facing AI disclosure present",
        "evidence_domain": "transparency_notice",
        "default_severity": "medium",
        "default_review_cycle_days": 365,
        "description": "Confirm users are clearly informed when they interact with an AI system or AI-generated content.",
        "suggested_evidence": ["Product disclosure copy", "Screenshot", "Help center notice"],
        "actor_roles": ["provider", "deployer"],
        "risk_tiers": ["transparency", "limited_risk"],
    },
    {
        "template_key": "bias_testing_performed",
        "article": "Article 15",
        "title": "Bias and performance testing performed",
        "evidence_domain": "testing_validation",
        "default_severity": "high",
        "default_review_cycle_days": 180,
        "description": "Track accuracy, robustness, bias, and cybersecurity testing evidence for the AI system.",
        "suggested_evidence": ["Test protocol", "Bias evaluation results", "Remediation log"],
        "actor_roles": ["provider"],
        "risk_tiers": ["high_risk"],
    },
    {
        "template_key": "incident_process_documented",
        "article": "Article 73",
        "title": "Serious incident process documented",
        "evidence_domain": "governance_incident",
        "default_severity": "critical",
        "default_review_cycle_days": 90,
        "description": "Confirm serious incident detection, triage, reporting deadlines, and authority notification paths are documented.",
        "suggested_evidence": ["Incident SOP", "Notification checklist", "Escalation contacts"],
        "actor_roles": ["provider", "deployer"],
        "risk_tiers": ["high_risk", "systemic"],
    },
    {
        "template_key": "data_governance_reviewed",
        "article": "Article 10",
        "title": "Data governance reviewed",
        "evidence_domain": "data_governance",
        "default_severity": "high",
        "default_review_cycle_days": 180,
        "description": "Confirm training, validation, and operational data governance controls are reviewed and documented.",
        "suggested_evidence": ["Dataset lineage", "Data quality review", "Privacy/DPIA linkage"],
        "actor_roles": ["provider"],
        "risk_tiers": ["high_risk"],
    },
    {
        "template_key": "model_limitations_documented",
        "article": "Article 13",
        "title": "Model limitations documented",
        "evidence_domain": "model_limitations",
        "default_severity": "medium",
        "default_review_cycle_days": 365,
        "description": "Capture intended purpose, known limitations, misuse boundaries, and instructions for deployers or users.",
        "suggested_evidence": ["Model card", "Instructions for use", "Known limitation register"],
        "actor_roles": ["provider"],
        "risk_tiers": ["high_risk", "gpai"],
    },
]


class ComplianceControlService:
    @staticmethod
    def _require_system(db: Session, tenant_id: str, ai_system_id: Optional[str]) -> None:
        if not ai_system_id:
            return
        exists = db.query(AiSystem.id).filter(AiSystem.tenant_id == tenant_id, AiSystem.id == ai_system_id).first()
        if not exists:
            raise HTTPException(status_code=404, detail="AI system not found for tenant")

    @staticmethod
    def _attach_evidence_metrics(db: Session, tenant_id: str, controls: List[ComplianceControl]) -> List[ComplianceControl]:
        control_ids = [control.id for control in controls]
        if not control_ids:
            return controls

        evidence_by_control: dict[str, list[EvidenceItem]] = {control_id: [] for control_id in control_ids}
        evidence_items = (
            db.query(EvidenceItem)
            .filter(
                EvidenceItem.tenant_id == tenant_id,
                EvidenceItem.control_id.in_(control_ids),
            )
            .all()
        )
        for item in evidence_items:
            if item.control_id in evidence_by_control:
                evidence_by_control[item.control_id].append(item)

        for control in controls:
            linked_items = evidence_by_control.get(control.id, [])
            status_counts = Counter(item.status for item in linked_items)
            latest_evidence_at = max((item.collected_at for item in linked_items if item.collected_at), default=None)
            details = _details(control)
            review_history = details.get("review_history") if isinstance(details.get("review_history"), list) else []
            comments = details.get("comments") if isinstance(details.get("comments"), list) else []
            last_reviewed_at = _parse_datetime(details.get("last_reviewed_at"))
            next_review_at = _parse_datetime(details.get("next_review_at"))
            now = datetime.now(timezone.utc)
            setattr(control, "evidence_item_count", len(linked_items))
            setattr(control, "active_evidence_count", status_counts.get("active", 0))
            setattr(control, "needs_review_evidence_count", status_counts.get("needs_review", 0))
            setattr(control, "latest_evidence_at", latest_evidence_at)
            setattr(control, "evidence_status_counts", dict(status_counts))
            setattr(control, "evidence_required", bool(control.evidence_domain))
            setattr(control, "evidence_complete", status_counts.get("active", 0) > 0)
            setattr(control, "severity", _severity_for_control(control, details))
            setattr(control, "review_cycle_days", _coerce_positive_int(details.get("review_cycle_days")))
            setattr(control, "last_reviewed_at", last_reviewed_at)
            setattr(control, "next_review_at", next_review_at)
            setattr(control, "review_overdue", bool(next_review_at and next_review_at < now))
            setattr(control, "last_review_note", details.get("last_review_note"))
            setattr(control, "review_history", review_history)
            setattr(control, "comment_count", len(comments))
            setattr(control, "latest_comment", comments[0].get("note") if comments and isinstance(comments[0], dict) else None)
        return controls

    @staticmethod
    def get_control(db: Session, tenant_id: str, control_id: str) -> ComplianceControl:
        control = db.query(ComplianceControl).filter(
            ComplianceControl.tenant_id == tenant_id,
            ComplianceControl.id == control_id,
        ).first()
        if not control:
            raise HTTPException(status_code=404, detail="Compliance control not found")
        ComplianceControlService._attach_evidence_metrics(db, tenant_id, [control])
        return control

    @staticmethod
    def list_controls(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> List[ComplianceControl]:
        query = db.query(ComplianceControl).filter(ComplianceControl.tenant_id == tenant_id)
        if ai_system_id:
            query = query.filter(ComplianceControl.ai_system_id == ai_system_id)
        controls = query.order_by(ComplianceControl.article.asc(), ComplianceControl.control_key.asc()).all()
        return ComplianceControlService._attach_evidence_metrics(db, tenant_id, controls)

    @staticmethod
    def list_templates(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> list[dict[str, Any]]:
        ComplianceControlService._require_system(db, tenant_id, ai_system_id)
        existing = (
            db.query(ComplianceControl)
            .filter(ComplianceControl.tenant_id == tenant_id, ComplianceControl.ai_system_id == ai_system_id)
            .all()
        )
        existing_by_key = {control.control_key: control.id for control in existing}
        templates: list[dict[str, Any]] = []
        for template in CONTROL_TEMPLATES:
            control_id = existing_by_key.get(template["template_key"])
            templates.append({
                **template,
                "applied": bool(control_id),
                "existing_control_id": control_id,
            })
        return templates

    @staticmethod
    def create_control(db: Session, tenant_id: str, payload: ComplianceControlCreate) -> ComplianceControl:
        ComplianceControlService._require_system(db, tenant_id, payload.ai_system_id)
        details = _normalized_details(payload.details_json)
        details["severity"] = payload.severity
        if payload.review_cycle_days is not None:
            details["review_cycle_days"] = payload.review_cycle_days
        if payload.next_review_at is not None:
            details["next_review_at"] = _isoformat(payload.next_review_at)

        control = ComplianceControl(
            id=f"ctl-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            ai_system_id=payload.ai_system_id,
            control_key=payload.control_key,
            article=payload.article,
            title=payload.title,
            owner_email=payload.owner_email,
            status=payload.status,
            due_at=payload.due_at,
            evidence_domain=payload.evidence_domain,
            details_json=details,
        )
        db.add(control)
        db.commit()
        db.refresh(control)
        ComplianceControlService._attach_evidence_metrics(db, tenant_id, [control])
        return control

    @staticmethod
    def apply_templates(
        db: Session,
        tenant_id: str,
        payload: ComplianceControlTemplateApplyRequest,
    ) -> List[ComplianceControl]:
        ComplianceControlService._require_system(db, tenant_id, payload.ai_system_id)
        if not payload.template_keys:
            raise HTTPException(status_code=400, detail="At least one control template key is required")

        templates_by_key = {template["template_key"]: template for template in CONTROL_TEMPLATES}
        unknown = [key for key in payload.template_keys if key not in templates_by_key]
        if unknown:
            raise HTTPException(status_code=404, detail=f"Unknown control template: {unknown[0]}")

        controls: list[ComplianceControl] = []
        seen: set[str] = set()
        for template_key in payload.template_keys:
            if template_key in seen:
                continue
            seen.add(template_key)
            template = templates_by_key[template_key]
            existing = db.query(ComplianceControl).filter(
                ComplianceControl.tenant_id == tenant_id,
                ComplianceControl.ai_system_id == payload.ai_system_id,
                ComplianceControl.control_key == template_key,
            ).first()
            if existing:
                controls.append(existing)
                continue

            control = ComplianceControl(
                id=f"ctl-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                ai_system_id=payload.ai_system_id,
                control_key=template["template_key"],
                article=template["article"],
                title=template["title"],
                owner_email=payload.owner_email,
                status="not_started",
                due_at=payload.due_at,
                evidence_domain=template["evidence_domain"],
                details_json={
                    "source": "control_template_catalog",
                    "template_key": template["template_key"],
                    "template_description": template["description"],
                    "suggested_evidence": template["suggested_evidence"],
                    "actor_roles": template["actor_roles"],
                    "risk_tiers": template["risk_tiers"],
                    "severity": template["default_severity"],
                    "review_cycle_days": template["default_review_cycle_days"],
                },
            )
            db.add(control)
            controls.append(control)

        db.commit()
        for control in controls:
            db.refresh(control)
        return ComplianceControlService._attach_evidence_metrics(db, tenant_id, controls)

    @staticmethod
    def update_control(db: Session, tenant_id: str, control_id: str, payload: ComplianceControlUpdate) -> ComplianceControl:
        control = ComplianceControlService.get_control(db, tenant_id, control_id)
        fields_set = getattr(payload, "model_fields_set", set())

        if "owner_email" in fields_set:
            control.owner_email = payload.owner_email
        if "status" in fields_set and payload.status is not None:
            control.status = payload.status
        if "due_at" in fields_set:
            control.due_at = payload.due_at

        details = _normalized_details(payload.details_json) if "details_json" in fields_set and payload.details_json is not None else _details(control)
        if "severity" in fields_set:
            if payload.severity is None:
                details.pop("severity", None)
            else:
                details["severity"] = payload.severity
        if "review_cycle_days" in fields_set:
            if payload.review_cycle_days is None:
                details.pop("review_cycle_days", None)
            else:
                details["review_cycle_days"] = payload.review_cycle_days
        if "next_review_at" in fields_set:
            if payload.next_review_at is None:
                details.pop("next_review_at", None)
            else:
                details["next_review_at"] = _isoformat(payload.next_review_at)
        control.details_json = details

        db.commit()
        db.refresh(control)
        ComplianceControlService._attach_evidence_metrics(db, tenant_id, [control])
        return control

    @staticmethod
    def record_review(
        db: Session,
        tenant_id: str,
        control_id: str,
        payload: ComplianceControlReviewCreate,
    ) -> ComplianceControl:
        control = ComplianceControlService.get_control(db, tenant_id, control_id)
        details = _details(control)
        now = datetime.now(timezone.utc)
        review_cycle_days = payload.review_cycle_days or _coerce_positive_int(details.get("review_cycle_days"))
        next_review_at = payload.next_review_at
        if next_review_at is None and review_cycle_days:
            next_review_at = now + timedelta(days=review_cycle_days)

        note = (payload.note or "").strip() or None
        event = {
            "reviewed_at": now.isoformat(),
            "reviewer_email": payload.reviewer_email,
            "outcome": payload.outcome,
            "note": note,
            "status": payload.status or control.status,
            "severity": payload.severity or _severity_for_control(control, details),
            "next_review_at": _isoformat(next_review_at) if next_review_at else None,
        }

        review_history = details.get("review_history") if isinstance(details.get("review_history"), list) else []
        details["review_history"] = [event, *review_history][:25]
        details["last_reviewed_at"] = now.isoformat()
        details["last_review_note"] = note
        details["last_review_outcome"] = payload.outcome
        if payload.reviewer_email:
            details["reviewer_email"] = payload.reviewer_email
        if payload.severity:
            details["severity"] = payload.severity
        if review_cycle_days:
            details["review_cycle_days"] = review_cycle_days
        if next_review_at:
            details["next_review_at"] = _isoformat(next_review_at)
        if note:
            comments = details.get("comments") if isinstance(details.get("comments"), list) else []
            details["comments"] = [
                {
                    "created_at": now.isoformat(),
                    "author_email": payload.reviewer_email,
                    "note": note,
                    "source": "control_review",
                },
                *comments,
            ][:50]
        if payload.status:
            control.status = payload.status

        control.details_json = details
        db.commit()
        db.refresh(control)
        ComplianceControlService._attach_evidence_metrics(db, tenant_id, [control])
        return control

    @staticmethod
    def seed_baseline(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> List[ComplianceControl]:
        ComplianceControlService._require_system(db, tenant_id, ai_system_id)
        created: list[ComplianceControl] = []
        for item in BASELINE_CONTROLS:
            existing = db.query(ComplianceControl).filter(
                ComplianceControl.tenant_id == tenant_id,
                ComplianceControl.ai_system_id == ai_system_id,
                ComplianceControl.control_key == item["control_key"],
            ).first()
            if existing:
                created.append(existing)
                continue

            control = ComplianceControl(
                id=f"ctl-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                ai_system_id=ai_system_id,
                status="not_started",
                details_json={
                    "source": "baseline_eu_ai_act_controls",
                    **BASELINE_LIFECYCLE.get(item["control_key"], {"severity": "medium", "review_cycle_days": 365}),
                },
                **item,
            )
            db.add(control)
            created.append(control)
        db.commit()
        for control in created:
            db.refresh(control)
        ComplianceControlService._attach_evidence_metrics(db, tenant_id, created)
        return created

    @staticmethod
    def seed_from_obligation_graph(
        db: Session,
        tenant_id: str,
        obligation_graph: list[dict],
        *,
        intake_id: str,
        obligation_path: str,
        ai_system_id: Optional[str] = None,
        commit: bool = True,
    ) -> List[ComplianceControl]:
        ComplianceControlService._require_system(db, tenant_id, ai_system_id)
        created: list[ComplianceControl] = []

        for item in obligation_graph:
            key = item.get("key")
            if not key:
                continue

            control_key = f"intake_{key}"
            existing = db.query(ComplianceControl).filter(
                ComplianceControl.tenant_id == tenant_id,
                ComplianceControl.ai_system_id == ai_system_id,
                ComplianceControl.control_key == control_key,
            ).first()
            if existing:
                created.append(existing)
                continue

            control = ComplianceControl(
                id=f"ctl-{uuid.uuid4().hex[:8]}",
                tenant_id=tenant_id,
                ai_system_id=ai_system_id,
                control_key=control_key,
                article=item.get("article") or "EU AI Act",
                title=item.get("summary") or key.replace("_", " ").title(),
                status=_status_from_obligation(item.get("status")),
                evidence_domain=item.get("evidence_domain") or "classification",
                details_json={
                    "source": "intake_obligation_graph",
                    "intake_id": intake_id,
                    "obligation_key": key,
                    "obligation_status": item.get("status"),
                    "obligation_path": obligation_path,
                    "owner_role": item.get("owner_role"),
                    "summary": item.get("summary"),
                    "penalty_exposure": item.get("penalty_exposure"),
                    "severity": _severity_from_obligation(item),
                    "review_cycle_days": 180 if item.get("status") in {"blocking", "review_required"} else 365,
                },
            )
            db.add(control)
            created.append(control)

        db.flush()
        if commit:
            db.commit()
            for control in created:
                db.refresh(control)
            ComplianceControlService._attach_evidence_metrics(db, tenant_id, created)
        return created

    @staticmethod
    def scorecard(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> dict:
        controls = ComplianceControlService.list_controls(db, tenant_id, ai_system_id)
        now = datetime.now(timezone.utc)
        completed = [c for c in controls if c.status in {"completed", "signed_off"}]
        overdue = [
            c for c in controls
            if c.due_at is not None and c.status not in {"completed", "signed_off"} and _aware(c.due_at) < now
        ]
        by_status: dict[str, int] = {}
        for control in controls:
            by_status[control.status] = by_status.get(control.status, 0) + 1

        score = 0 if not controls else round((len(completed) / len(controls)) * 100)
        return {
            "tenant_id": tenant_id,
            "ai_system_id": ai_system_id,
            "total_controls": len(controls),
            "completed_controls": len(completed),
            "overdue_controls": len(overdue),
            "readiness_score": score,
            "controls_by_status": by_status,
        }

    @staticmethod
    def audit_status(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> dict[str, Any]:
        controls = ComplianceControlService.list_controls(db, tenant_id, ai_system_id)
        now = datetime.now(timezone.utc)
        completed_statuses = {"completed", "signed_off"}
        rows = [_audit_row(control) for control in controls]
        completed = [row for row in rows if row["status"] in completed_statuses]
        incomplete = [row for row in rows if row["status"] not in completed_statuses]
        evidence_gaps = [row for row in rows if row["evidence_required"] and not row["evidence_complete"]]
        owner_gaps = [row for row in rows if not row["owner_email"]]
        due_overdue = [
            row for row in rows
            if row["due_at"] and row["status"] not in completed_statuses and _parse_datetime(row["due_at"]) and _parse_datetime(row["due_at"]) < now
        ]
        review_overdue = [row for row in rows if row["review_overdue"]]
        high_severity_open = [
            row for row in rows
            if row["severity"] in {"high", "critical"} and row["status"] not in completed_statuses
        ]
        readiness_score = 0 if not rows else round((len(completed) / len(rows)) * 100)
        summary = {
            "total_controls": len(rows),
            "completed_controls": len(completed),
            "incomplete_controls": len(incomplete),
            "readiness_score": readiness_score,
            "evidence_gap_controls": len(evidence_gaps),
            "missing_owner_controls": len(owner_gaps),
            "overdue_controls": len(due_overdue),
            "review_overdue_controls": len(review_overdue),
            "high_severity_open_controls": len(high_severity_open),
        }
        generated_at = now
        return {
            "tenant_id": tenant_id,
            "ai_system_id": ai_system_id,
            "generated_at": generated_at,
            "summary": summary,
            "controls": rows,
            "markdown": _render_audit_markdown(tenant_id, ai_system_id, generated_at, summary, rows),
        }


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _details(control: ComplianceControl) -> dict[str, Any]:
    return _normalized_details(control.details_json)


def _normalized_details(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return _aware(value)
    if isinstance(value, str) and value.strip():
        try:
            return _aware(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def _isoformat(value: datetime) -> str:
    return _aware(value).isoformat()


def _coerce_positive_int(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _severity_for_control(control: ComplianceControl, details: dict[str, Any]) -> str:
    severity = details.get("severity")
    if severity in {"low", "medium", "high", "critical"}:
        return severity
    return _severity_from_obligation({"status": control.status, "penalty_exposure": details.get("penalty_exposure")})


def _severity_from_obligation(item: dict[str, Any]) -> str:
    penalty = item.get("penalty_exposure") or {}
    max_eur = penalty.get("max_eur") if isinstance(penalty, dict) else None
    if item.get("status") == "blocking":
        return "high"
    if isinstance(max_eur, int) and max_eur >= 35_000_000:
        return "critical"
    if isinstance(max_eur, int) and max_eur >= 15_000_000:
        return "high"
    return "medium"


def _audit_row(control: ComplianceControl) -> dict[str, Any]:
    details = _details(control)
    evidence_item_count = getattr(control, "evidence_item_count", 0)
    evidence_complete = bool(getattr(control, "evidence_complete", False))
    review_overdue = bool(getattr(control, "review_overdue", False))
    return {
        "id": control.id,
        "control_key": control.control_key,
        "article": control.article,
        "title": control.title,
        "owner_email": control.owner_email,
        "status": control.status,
        "severity": getattr(control, "severity", _severity_for_control(control, details)),
        "due_at": _isoformat(control.due_at) if control.due_at else None,
        "evidence_domain": control.evidence_domain,
        "evidence_required": bool(getattr(control, "evidence_required", True)),
        "evidence_complete": evidence_complete,
        "evidence_item_count": evidence_item_count,
        "active_evidence_count": getattr(control, "active_evidence_count", 0),
        "latest_evidence_at": _isoformat(getattr(control, "latest_evidence_at")) if getattr(control, "latest_evidence_at", None) else None,
        "review_cycle_days": getattr(control, "review_cycle_days", None),
        "last_reviewed_at": _isoformat(getattr(control, "last_reviewed_at")) if getattr(control, "last_reviewed_at", None) else None,
        "next_review_at": _isoformat(getattr(control, "next_review_at")) if getattr(control, "next_review_at", None) else None,
        "review_overdue": review_overdue,
        "latest_comment": getattr(control, "latest_comment", None),
        "audit_ready": control.status in {"completed", "signed_off"} and evidence_complete and not review_overdue,
    }


def _render_audit_markdown(
    tenant_id: str,
    ai_system_id: Optional[str],
    generated_at: datetime,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
) -> str:
    scope = ai_system_id or "tenant-wide"
    lines = [
        "# Compliance Control Audit Status",
        "",
        f"- Tenant: `{tenant_id}`",
        f"- Scope: `{scope}`",
        f"- Generated: `{generated_at.isoformat()}`",
        f"- Readiness score: `{summary['readiness_score']}%`",
        f"- Controls: `{summary['completed_controls']}/{summary['total_controls']} completed`",
        f"- Evidence gaps: `{summary['evidence_gap_controls']}`",
        f"- Missing owners: `{summary['missing_owner_controls']}`",
        f"- Overdue controls: `{summary['overdue_controls']}`",
        f"- Review overdue: `{summary['review_overdue_controls']}`",
        "",
        "| Control | Article | Owner | Status | Severity | Evidence | Due | Review | Audit Ready |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        evidence = f"{row['active_evidence_count']}/{row['evidence_item_count']}" if row["evidence_required"] else "not required"
        review = row["next_review_at"][:10] if row.get("next_review_at") else "not set"
        due = row["due_at"][:10] if row.get("due_at") else "not set"
        ready = "yes" if row["audit_ready"] else "no"
        owner = row["owner_email"] or "unassigned"
        title = str(row["title"]).replace("|", "\\|")
        lines.append(
            f"| {title} | {row['article']} | {owner} | {row['status']} | {row['severity']} | {evidence} | {due} | {review} | {ready} |"
        )
    if not rows:
        lines.append("| No controls in scope | - | - | - | - | - | - | - | no |")
    return "\n".join(lines) + "\n"


def _status_from_obligation(status: Optional[str]) -> str:
    if status in {"blocking", "review_required"}:
        return "blocked"
    return "not_started"
