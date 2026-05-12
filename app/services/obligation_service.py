import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import FRIARecord, OversightAssignment, IncidentRecord, AiSystem
from app.schemas import FRIACreate, FRIAUpdate, OversightCreate, OversightUpdate, IncidentCreate, IncidentUpdate
from app.services.entitlement_service import check_entitlement
from app.services.evidence_service import write_evidence_log
from app.services.regulatory_knowledge import article_refs, serious_incident_deadline

class ObligationService:
    @staticmethod
    def _require_tenant_system(db: Session, tenant_id: str, ai_system_id: str) -> AiSystem:
        system = db.query(AiSystem).filter(
            AiSystem.tenant_id == tenant_id,
            AiSystem.id == ai_system_id,
        ).first()
        if not system:
            raise HTTPException(status_code=404, detail="AI system not found for tenant")
        return system

    # --- FRIA ---
    @staticmethod
    def list_frias(db: Session, tenant_id: str) -> List[FRIARecord]:
        if not check_entitlement(db, tenant_id, "fria_management"):
            raise HTTPException(status_code=403, detail="FRIA management not entitled for this tenant")
        return db.query(FRIARecord).filter(FRIARecord.tenant_id == tenant_id).all()

    @staticmethod
    def get_fria(db: Session, tenant_id: str, fria_id: str) -> FRIARecord:
        if not check_entitlement(db, tenant_id, "fria_management"):
            raise HTTPException(status_code=403, detail="FRIA management not entitled for this tenant")
        fria = db.query(FRIARecord).filter(FRIARecord.tenant_id == tenant_id, FRIARecord.id == fria_id).first()
        if not fria:
            raise HTTPException(status_code=404, detail="FRIA record not found")
        return fria

    @staticmethod
    def create_fria(db: Session, tenant_id: str, payload: FRIACreate) -> FRIARecord:
        if not check_entitlement(db, tenant_id, "fria_management"):
            raise HTTPException(status_code=403, detail="FRIA management not entitled for this tenant")
        ObligationService._require_tenant_system(db, tenant_id, payload.ai_system_id)
        
        fria = FRIARecord(
            id=f"fria-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            ai_system_id=payload.ai_system_id,
            status=payload.status,
            assessment_json=payload.assessment_json,
            legal_basis_json=article_refs("art_27"),
            dpia_link_json=payload.dpia_link_json,
            signoff_json=payload.signoff_json,
        )
        db.add(fria)
        
        # Log Evidence
        write_evidence_log(db, {
            "tenant_id": tenant_id,
            "ai_system_id": payload.ai_system_id,
            "evidence_domain": "governance_fria",
            "event_type": "fria_created",
            "request_id": f"req-{uuid.uuid4().hex[:8]}",
            "trace_id": f"trc-{uuid.uuid4().hex[:8]}",
            "decision": "recorded",
            "status": "success",
            "risk_level": "none",
            "risk_score": 0,
            "metadata": {"fria_id": fria.id}
        })
        
        db.commit()
        db.refresh(fria)
        return fria

    @staticmethod
    def update_fria(db: Session, tenant_id: str, fria_id: str, payload: FRIAUpdate) -> FRIARecord:
        fria = ObligationService.get_fria(db, tenant_id, fria_id)
        if payload.status is not None:
            fria.status = payload.status
        if payload.assessment_json is not None:
            fria.assessment_json = payload.assessment_json
        if payload.dpia_link_json is not None:
            fria.dpia_link_json = payload.dpia_link_json
        if payload.signoff_json is not None:
            fria.signoff_json = payload.signoff_json
        
        db.commit()
        db.refresh(fria)
        return fria

    @staticmethod
    def delete_fria(db: Session, tenant_id: str, fria_id: str):
        fria = ObligationService.get_fria(db, tenant_id, fria_id)
        db.delete(fria)
        db.commit()
        return {"status": "deleted"}

    # --- Oversight ---
    @staticmethod
    def list_oversight(db: Session, tenant_id: str) -> List[OversightAssignment]:
        if not check_entitlement(db, tenant_id, "oversight_management"):
            raise HTTPException(status_code=403, detail="Oversight management not entitled for this tenant")
        return db.query(OversightAssignment).filter(OversightAssignment.tenant_id == tenant_id).all()

    @staticmethod
    def create_oversight(db: Session, tenant_id: str, payload: OversightCreate) -> OversightAssignment:
        if not check_entitlement(db, tenant_id, "oversight_management"):
            raise HTTPException(status_code=403, detail="Oversight management not entitled for this tenant")
        ObligationService._require_tenant_system(db, tenant_id, payload.ai_system_id)
        
        assignment = OversightAssignment(
            id=f"ovs-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            ai_system_id=payload.ai_system_id,
            reviewer_email=payload.reviewer_email,
            role=payload.role,
            competence_json=payload.competence_json,
        )
        db.add(assignment)
        
        # Log Evidence
        write_evidence_log(db, {
            "tenant_id": tenant_id,
            "ai_system_id": payload.ai_system_id,
            "evidence_domain": "governance_oversight",
            "event_type": "oversight_assigned",
            "request_id": f"req-{uuid.uuid4().hex[:8]}",
            "trace_id": f"trc-{uuid.uuid4().hex[:8]}",
            "decision": "recorded",
            "status": "success",
            "risk_level": "none",
            "risk_score": 0,
            "metadata": {"assignment_id": assignment.id, "reviewer_email": payload.reviewer_email}
        })
        
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def update_oversight(db: Session, tenant_id: str, assignment_id: str, payload: OversightUpdate) -> OversightAssignment:
        if not check_entitlement(db, tenant_id, "oversight_management"):
            raise HTTPException(status_code=403, detail="Oversight management not entitled for this tenant")
        
        assignment = db.query(OversightAssignment).filter(OversightAssignment.tenant_id == tenant_id, OversightAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Oversight assignment not found")
        
        if payload.reviewer_email is not None:
            assignment.reviewer_email = payload.reviewer_email
        if payload.role is not None:
            assignment.role = payload.role
        if payload.competence_json is not None:
            assignment.competence_json = payload.competence_json
            
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def delete_oversight(db: Session, tenant_id: str, assignment_id: str):
        if not check_entitlement(db, tenant_id, "oversight_management"):
            raise HTTPException(status_code=403, detail="Oversight management not entitled for this tenant")
        
        assignment = db.query(OversightAssignment).filter(OversightAssignment.tenant_id == tenant_id, OversightAssignment.id == assignment_id).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Oversight assignment not found")
            
        db.delete(assignment)
        db.commit()
        return {"status": "deleted"}

    # --- Incidents ---
    @staticmethod
    def list_incidents(db: Session, tenant_id: str) -> List[IncidentRecord]:
        if not check_entitlement(db, tenant_id, "incident_management"):
            raise HTTPException(status_code=403, detail="Incident management not entitled for this tenant")
        return db.query(IncidentRecord).filter(IncidentRecord.tenant_id == tenant_id).all()

    @staticmethod
    def get_incident(db: Session, tenant_id: str, incident_id: str) -> IncidentRecord:
        if not check_entitlement(db, tenant_id, "incident_management"):
            raise HTTPException(status_code=403, detail="Incident management not entitled for this tenant")
        incident = db.query(IncidentRecord).filter(IncidentRecord.tenant_id == tenant_id, IncidentRecord.id == incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident record not found")
        return incident

    @staticmethod
    def create_incident(db: Session, tenant_id: str, payload: IncidentCreate) -> IncidentRecord:
        if not check_entitlement(db, tenant_id, "incident_management"):
            raise HTTPException(status_code=403, detail="Incident management not entitled for this tenant")
        ObligationService._require_tenant_system(db, tenant_id, payload.ai_system_id)
        
        incident = IncidentRecord(
            id=f"inc-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            ai_system_id=payload.ai_system_id,
            severity=payload.severity,
            incident_type=payload.incident_type,
            description=payload.description,
            status=payload.status,
            deadline_at=serious_incident_deadline(None, payload.incident_type),
            escalation_status="open",
            authority_notification_json=payload.authority_notification_json,
        )
        db.add(incident)
        
        # Log Evidence
        write_evidence_log(db, {
            "tenant_id": tenant_id,
            "ai_system_id": payload.ai_system_id,
            "evidence_domain": "governance_incident",
            "event_type": "incident_reported",
            "request_id": f"req-{uuid.uuid4().hex[:8]}",
            "trace_id": f"trc-{uuid.uuid4().hex[:8]}",
            "decision": "recorded",
            "status": "success",
            "risk_level": payload.severity,
            "risk_score": 50 if payload.severity == "medium" else (80 if payload.severity == "high" else 20),
            "metadata": {"incident_id": incident.id}
        })
        
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def update_incident(db: Session, tenant_id: str, incident_id: str, payload: IncidentUpdate) -> IncidentRecord:
        incident = ObligationService.get_incident(db, tenant_id, incident_id)
        if payload.severity is not None:
            incident.severity = payload.severity
        if payload.incident_type is not None:
            incident.incident_type = payload.incident_type
            incident.deadline_at = serious_incident_deadline(incident.created_at, payload.incident_type)
        if payload.description is not None:
            incident.description = payload.description
        if payload.status is not None:
            incident.status = payload.status
        if payload.reported_at is not None:
            incident.reported_at = payload.reported_at
        if payload.escalation_status is not None:
            incident.escalation_status = payload.escalation_status
        if payload.authority_notification_json is not None:
            incident.authority_notification_json = payload.authority_notification_json
            
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def delete_incident(db: Session, tenant_id: str, incident_id: str):
        incident = ObligationService.get_incident(db, tenant_id, incident_id)
        db.delete(incident)
        db.commit()
        return {"status": "deleted"}
