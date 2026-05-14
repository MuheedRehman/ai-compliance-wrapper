import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import (
    AiFeature,
    AiSystem,
    ComplianceControl,
    EvidenceLog,
    FRIARecord,
    IncidentRecord,
    IntakeAssessment,
    OversightAssignment,
    ReportRecord,
    WebsiteScan,
)
from app.schemas import AiSystemCreate, AiSystemUpdate
from app.services.compliance_control_service import ComplianceControlService

def create_ai_system(db: Session, tenant_id: str, payload: AiSystemCreate) -> AiSystem:
    ai_system = AiSystem(
        id=f"sys-{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        # DB defaults will handle deployment_status and registration_status if not provided
    )
    db.add(ai_system)
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
    for key, value in update_data.items():
        setattr(ai_system, key, value)
    
    db.commit()
    db.refresh(ai_system)
    return ai_system


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

    latest_intake = intakes[0] if intakes else None
    open_incidents = [incident for incident in incidents if incident.status not in {"resolved", "closed"}]
    high_severity_incidents = [incident for incident in incidents if incident.severity in {"high", "critical"}]
    open_controls = [control for control in controls if control.status not in {"completed", "signed_off"}]

    return {
        "system": system,
        "metrics": {
            "feature_count": len(features),
            "control_count": len(controls),
            "open_control_count": len(open_controls),
            "evidence_log_count": len(evidence_logs),
            "website_scan_count": len(website_scans),
            "report_count": len(reports),
            "fria_count": len(fria_records),
            "oversight_count": len(oversight_assignments),
            "incident_count": len(incidents),
            "open_incident_count": len(open_incidents),
            "high_severity_incident_count": len(high_severity_incidents),
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
        "evidence_logs": evidence_logs,
        "website_scans": website_scans,
        "intakes": intakes,
        "fria_records": fria_records,
        "oversight_assignments": oversight_assignments,
        "incidents": incidents,
        "reports": reports,
    }
