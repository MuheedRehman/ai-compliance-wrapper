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
    WebsiteScan,
)
from app.schemas import AiSystemCreate, AiSystemReviewCreate, AiSystemUpdate
from app.services.compliance_control_service import ComplianceControlService


def _normalize_email(value: str | None) -> str | None:
    cleaned = (value or "").strip().lower()
    return cleaned or None


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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
        },
        "governance_summary": {
            "owner_roles": owner_roles,
            "assigned_owner_count": assigned_owner_count,
            "missing_owner_roles": [role for role, email in owner_roles.items() if not email],
            "review_deadline_status": review_deadline_status,
            "next_review_at": system.next_review_at,
            "last_reviewed_at": system.last_reviewed_at,
            "latest_review_status": system.review_status,
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
    }
