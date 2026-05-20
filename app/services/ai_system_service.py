import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import (
    AiFeature,
    AiSystem,
    AiSystemReviewEvent,
    ComplianceControl,
    EvidenceItem,
    EvidenceLog,
    FRIARecord,
    IncidentRecord,
    IntakeAssessment,
    OversightAssignment,
    ReportRecord,
    ReviewTask,
    WebsiteScan,
)
from app.schemas import AiSystemCreate, AiSystemReviewCreate, AiSystemUpdate
from app.services.compliance_control_service import ComplianceControlService
from app.services.review_service import get_or_create_open_review_task


def _normalize_email(value: str | None) -> str | None:
    cleaned = (value or "").strip().lower()
    return cleaned or None


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _coerce_datetime(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, str):
        try:
            return _normalize_datetime(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _review_deadline_status(system: AiSystem) -> str:
    due_at = _normalize_datetime(system.next_review_at)
    if not due_at:
        return "unscheduled"
    now = _now_utc()
    if due_at < now:
        return "overdue"
    if due_at <= now + timedelta(days=30):
        return "due_soon"
    return "scheduled"


def _action_target_type(action: dict) -> str:
    target_type = str(action.get("target_type") or "").strip().lower()
    if target_type in {"control", "evidence", "general"}:
        return target_type
    if action.get("control_id"):
        return "control"
    if action.get("evidence_item_id") or action.get("evidence_type"):
        return "evidence"
    return "general"


def _validate_follow_up_links(db: Session, tenant_id: str, ai_system_id: str, action: dict) -> None:
    control_id = action.get("control_id")
    if control_id:
        control = (
            db.query(ComplianceControl)
            .filter(ComplianceControl.tenant_id == tenant_id, ComplianceControl.id == control_id)
            .first()
        )
        if not control:
            raise HTTPException(status_code=404, detail="Follow-up control not found")
        if control.ai_system_id and control.ai_system_id != ai_system_id:
            raise HTTPException(status_code=400, detail="Follow-up control belongs to a different AI system")

    evidence_item_id = action.get("evidence_item_id")
    if evidence_item_id:
        evidence = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.tenant_id == tenant_id, EvidenceItem.id == evidence_item_id)
            .first()
        )
        if not evidence:
            raise HTTPException(status_code=404, detail="Follow-up evidence item not found")
        if evidence.ai_system_id and evidence.ai_system_id != ai_system_id:
            raise HTTPException(status_code=400, detail="Follow-up evidence item belongs to a different AI system")


def _normalize_follow_up_action(action: dict, index: int) -> dict:
    title = str(
        action.get("title")
        or action.get("summary")
        or action.get("description")
        or f"Review follow-up action {index + 1}"
    ).strip()
    severity = str(action.get("severity") or "medium").strip().lower()
    if severity not in {"low", "medium", "high", "critical"}:
        severity = "medium"
    target_type = _action_target_type(action)
    due_at = _coerce_datetime(action.get("due_at") or action.get("due_date"))
    normalized = {
        **action,
        "title": title,
        "description": action.get("description") or action.get("summary"),
        "target_type": target_type,
        "severity": severity,
        "owner_email": _normalize_email(action.get("owner_email")),
        "due_at": due_at.isoformat() if due_at else None,
    }
    if target_type == "control":
        normalized["target_route"] = "controls"
    elif target_type == "evidence":
        normalized["target_route"] = "evidence"
    else:
        normalized["target_route"] = "reviews"
    return normalized


def _create_follow_up_tasks(
    db: Session,
    tenant_id: str,
    ai_system_id: str,
    event: AiSystemReviewEvent,
    actions: list[dict],
) -> list[dict]:
    linked_actions: list[dict] = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        normalized = _normalize_follow_up_action(action, index)
        _validate_follow_up_links(db, tenant_id, ai_system_id, normalized)
        trigger_reason = f"ai_system_review_follow_up:{event.id}:{index}"
        task = get_or_create_open_review_task(
            db=db,
            tenant_id=tenant_id,
            feature_id=None,
            review_type="ai_system_lifecycle_follow_up",
            trigger_reason=trigger_reason,
            severity=normalized["severity"],
            findings={
                "source": "ai_system_review_event",
                "source_review_event_id": event.id,
                "action_index": index,
                "title": normalized["title"],
                "description": normalized.get("description"),
                "target_type": normalized["target_type"],
                "target_route": normalized["target_route"],
                "control_id": normalized.get("control_id"),
                "evidence_item_id": normalized.get("evidence_item_id"),
                "owner_email": normalized.get("owner_email"),
                "due_at": normalized.get("due_at"),
                "review_type": event.review_type,
            },
            ai_system_id=ai_system_id,
        )
        linked_actions.append({
            **normalized,
            "review_task_id": task.review_task_id,
            "task_status": task.status,
        })
    return linked_actions


def create_ai_system(db: Session, tenant_id: str, payload: AiSystemCreate, *, commit: bool = True) -> AiSystem:
    ai_system = AiSystem(
        id=f"sys-{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        owner_email=_normalize_email(payload.owner_email),
        technical_owner_email=_normalize_email(payload.technical_owner_email),
        legal_owner_email=_normalize_email(payload.legal_owner_email),
        review_status=payload.review_status,
        next_review_at=_normalize_datetime(payload.next_review_at),
        lifecycle_notes=payload.lifecycle_notes,
        # DB defaults will handle deployment_status and registration_status if not provided
    )
    db.add(ai_system)
    db.flush()
    if commit:
        db.commit()
        db.refresh(ai_system)
    return ai_system

def list_ai_systems(db: Session, tenant_id: str):
    return db.query(AiSystem).filter(AiSystem.tenant_id == tenant_id).order_by(AiSystem.created_at.desc()).all()

def get_ai_system(db: Session, tenant_id: str, ai_system_id: str) -> AiSystem:
    ai_system = db.query(AiSystem).filter(AiSystem.tenant_id == tenant_id, AiSystem.id == ai_system_id).first()
    if not ai_system:
        raise HTTPException(status_code=404, detail="AI System not found")
    return ai_system

def update_ai_system(db: Session, tenant_id: str, ai_system_id: str, payload: AiSystemUpdate) -> AiSystem:
    ai_system = get_ai_system(db, tenant_id, ai_system_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    for email_field in ("owner_email", "technical_owner_email", "legal_owner_email"):
        if email_field in update_data:
            update_data[email_field] = _normalize_email(update_data[email_field])
    for date_field in ("next_review_at", "last_reviewed_at"):
        if date_field in update_data:
            update_data[date_field] = _normalize_datetime(update_data[date_field])
    for key, value in update_data.items():
        setattr(ai_system, key, value)
    
    db.commit()
    db.refresh(ai_system)
    return ai_system


def list_ai_system_reviews(db: Session, tenant_id: str, ai_system_id: str, limit: int = 25) -> list[AiSystemReviewEvent]:
    get_ai_system(db, tenant_id, ai_system_id)
    safe_limit = min(max(limit, 1), 100)
    return (
        db.query(AiSystemReviewEvent)
        .filter(AiSystemReviewEvent.tenant_id == tenant_id, AiSystemReviewEvent.ai_system_id == ai_system_id)
        .order_by(AiSystemReviewEvent.created_at.desc())
        .limit(safe_limit)
        .all()
    )


def record_ai_system_review(
    db: Session,
    tenant_id: str,
    ai_system_id: str,
    payload: AiSystemReviewCreate,
) -> AiSystemReviewEvent:
    system = get_ai_system(db, tenant_id, ai_system_id)
    now = _now_utc()
    event = AiSystemReviewEvent(
        id=f"rev_{uuid.uuid4().hex}",
        tenant_id=tenant_id,
        ai_system_id=ai_system_id,
        reviewer_email=_normalize_email(payload.reviewer_email),
        review_type=payload.review_type,
        status=payload.status,
        notes=payload.notes,
        findings_json=payload.findings,
        actions_json=payload.actions,
        next_review_at=_normalize_datetime(payload.next_review_at),
    )
    db.add(event)
    event.actions_json = _create_follow_up_tasks(db, tenant_id, ai_system_id, event, payload.actions)

    if payload.status == "completed":
        system.review_status = "completed"
        system.last_reviewed_at = now
    elif payload.status == "needs_follow_up":
        system.review_status = "in_review"
        system.last_reviewed_at = now
    else:
        system.review_status = payload.status

    if event.next_review_at:
        system.next_review_at = event.next_review_at

    db.commit()
    db.refresh(event)
    db.refresh(system)
    return event


def get_ai_system_workspace(db: Session, tenant_id: str, ai_system_id: str) -> dict:
    system = get_ai_system(db, tenant_id, ai_system_id)

    features = (
        db.query(AiFeature)
        .filter(AiFeature.tenant_id == tenant_id, AiFeature.ai_system_id == ai_system_id)
        .order_by(AiFeature.created_at.desc())
        .all()
    )
    controls = ComplianceControlService.list_controls(db, tenant_id, ai_system_id)
    scorecard = ComplianceControlService.scorecard(db, tenant_id, ai_system_id)
    evidence_logs = (
        db.query(EvidenceLog)
        .filter(EvidenceLog.tenant_id == tenant_id, EvidenceLog.ai_system_id == ai_system_id)
        .order_by(EvidenceLog.created_at.desc())
        .limit(25)
        .all()
    )
    evidence_items = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.tenant_id == tenant_id, EvidenceItem.ai_system_id == ai_system_id)
        .order_by(EvidenceItem.created_at.desc())
        .limit(25)
        .all()
    )
    website_scans = (
        db.query(WebsiteScan)
        .filter(WebsiteScan.tenant_id == tenant_id, WebsiteScan.ai_system_id == ai_system_id)
        .order_by(WebsiteScan.created_at.desc())
        .all()
    )
    intake_ids = [scan.intake_id for scan in website_scans if scan.intake_id]
    intakes = []
    if intake_ids:
        intakes = (
            db.query(IntakeAssessment)
            .filter(IntakeAssessment.tenant_id == tenant_id, IntakeAssessment.id.in_(intake_ids))
            .order_by(IntakeAssessment.created_at.desc())
            .all()
        )
    fria_records = (
        db.query(FRIARecord)
        .filter(FRIARecord.tenant_id == tenant_id, FRIARecord.ai_system_id == ai_system_id)
        .order_by(FRIARecord.created_at.desc())
        .all()
    )
    oversight_assignments = (
        db.query(OversightAssignment)
        .filter(OversightAssignment.tenant_id == tenant_id, OversightAssignment.ai_system_id == ai_system_id)
        .order_by(OversightAssignment.created_at.desc())
        .all()
    )
    incidents = (
        db.query(IncidentRecord)
        .filter(IncidentRecord.tenant_id == tenant_id, IncidentRecord.ai_system_id == ai_system_id)
        .order_by(IncidentRecord.created_at.desc())
        .all()
    )
    reports = (
        db.query(ReportRecord)
        .filter(ReportRecord.tenant_id == tenant_id, ReportRecord.ai_system_id == ai_system_id)
        .order_by(ReportRecord.created_at.desc())
        .all()
    )
    review_events = (
        db.query(AiSystemReviewEvent)
        .filter(AiSystemReviewEvent.tenant_id == tenant_id, AiSystemReviewEvent.ai_system_id == ai_system_id)
        .order_by(AiSystemReviewEvent.created_at.desc())
        .limit(25)
        .all()
    )
    follow_up_tasks = (
        db.query(ReviewTask)
        .filter(
            ReviewTask.tenant_id == tenant_id,
            ReviewTask.ai_system_id == ai_system_id,
            ReviewTask.review_type == "ai_system_lifecycle_follow_up",
        )
        .order_by(ReviewTask.created_at.desc())
        .limit(50)
        .all()
    )

    latest_intake = intakes[0] if intakes else None
    open_incidents = [incident for incident in incidents if incident.status not in {"resolved", "closed"}]
    high_severity_incidents = [incident for incident in incidents if incident.severity in {"high", "critical"}]
    open_controls = [control for control in controls if control.status not in {"completed", "signed_off"}]
    owner_roles = {
        "business_owner": system.owner_email,
        "technical_owner": system.technical_owner_email,
        "legal_owner": system.legal_owner_email,
    }
    assigned_owner_count = len([email for email in owner_roles.values() if email])
    review_deadline_status = _review_deadline_status(system)
    open_follow_up_tasks = [task for task in follow_up_tasks if task.status == "open"]
    linked_follow_up_tasks = [
        task for task in follow_up_tasks
        if (task.findings_json or {}).get("target_type") in {"control", "evidence"}
    ]

    return {
        "system": system,
        "metrics": {
            "feature_count": len(features),
            "control_count": len(controls),
            "open_control_count": len(open_controls),
            "evidence_item_count": len(evidence_items),
            "evidence_log_count": len(evidence_logs),
            "website_scan_count": len(website_scans),
            "report_count": len(reports),
            "fria_count": len(fria_records),
            "oversight_count": len(oversight_assignments),
            "incident_count": len(incidents),
            "open_incident_count": len(open_incidents),
            "high_severity_incident_count": len(high_severity_incidents),
            "review_event_count": len(review_events),
            "assigned_owner_count": assigned_owner_count,
            "follow_up_task_count": len(follow_up_tasks),
            "open_follow_up_task_count": len(open_follow_up_tasks),
            "linked_follow_up_task_count": len(linked_follow_up_tasks),
        },
        "governance_summary": {
            "owner_roles": owner_roles,
            "assigned_owner_count": assigned_owner_count,
            "missing_owner_roles": [role for role, email in owner_roles.items() if not email],
            "review_deadline_status": review_deadline_status,
            "next_review_at": system.next_review_at,
            "last_reviewed_at": system.last_reviewed_at,
            "latest_review_status": system.review_status,
            "open_follow_up_task_count": len(open_follow_up_tasks),
        },
        "readiness_scorecard": scorecard,
        "latest_classification": (
            {
                "intake_id": latest_intake.id,
                "actor_role": latest_intake.actor_role,
                "system_classification": latest_intake.system_classification,
                "obligation_path": latest_intake.obligation_path,
                "rationale": latest_intake.rationale,
                "legal_basis": latest_intake.legal_basis_json or [],
                "evidence_requirements": latest_intake.evidence_requirements_json or [],
                "created_at": latest_intake.created_at,
            }
            if latest_intake
            else None
        ),
        "features": features,
        "controls": controls,
        "evidence_items": evidence_items,
        "evidence_logs": evidence_logs,
        "website_scans": website_scans,
        "intakes": intakes,
        "fria_records": fria_records,
        "oversight_assignments": oversight_assignments,
        "incidents": incidents,
        "reports": reports,
        "review_events": review_events,
        "follow_up_tasks": follow_up_tasks,
    }
