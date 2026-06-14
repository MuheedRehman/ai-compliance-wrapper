import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import FRIARecord, OversightAssignment, IncidentRecord, AiSystem
from app.schemas import (
    FRIACreate, FRIAUpdate, FRIASectionsUpdate, FRIASubmitRequest, FRIAReviewRequest,
    OversightCreate, OversightUpdate, IncidentCreate, IncidentUpdate,
)
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

    # FRIA Builder helpers
    _FRIA_SECTIONS = [
        "intended_purpose",
        "affected_persons",
        "fundamental_rights_risks",
        "mitigation_measures",
        "human_oversight",
        "residual_risk",
    ]

    @staticmethod
    def _compute_completion(sections_json: dict) -> int:
        complete = sum(
            1 for s in ObligationService._FRIA_SECTIONS
            if s in sections_json and any(
                v for v in sections_json[s].values() if isinstance(v, str) and v.strip()
            )
        )
        return round(complete / len(ObligationService._FRIA_SECTIONS) * 100)

    @staticmethod
    def update_fria_sections(db: Session, tenant_id: str, fria_id: str, payload: FRIASectionsUpdate) -> FRIARecord:
        fria = ObligationService.get_fria(db, tenant_id, fria_id)
        if fria.status not in ("draft", "rejected"):
            raise HTTPException(status_code=409, detail="Sections can only be edited in draft or rejected state")
        merged = dict(fria.sections_json or {})
        for section in ObligationService._FRIA_SECTIONS:
            value = getattr(payload, section)
            if value is not None:
                merged[section] = value
        fria.sections_json = merged
        fria.completion_percent = ObligationService._compute_completion(merged)
        db.commit()
        db.refresh(fria)
        return fria

    @staticmethod
    def submit_fria(db: Session, tenant_id: str, fria_id: str, payload: FRIASubmitRequest) -> FRIARecord:
        fria = ObligationService.get_fria(db, tenant_id, fria_id)
        if fria.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft FRIAs can be submitted for review")
        fria.status = "in_review"
        import datetime as _dt
        fria.approval_json = {
            "submitted_by": payload.submitted_by,
            "submitted_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "reviewed_by": None,
            "reviewed_at": None,
            "outcome": None,
            "notes": None,
        }
        write_evidence_log(db, {
            "tenant_id": tenant_id,
            "ai_system_id": fria.ai_system_id,
            "evidence_domain": "governance_fria",
            "event_type": "fria_submitted",
            "request_id": f"req-{uuid.uuid4().hex[:8]}",
            "trace_id": f"trc-{uuid.uuid4().hex[:8]}",
            "decision": "pending_review",
            "status": "success",
            "risk_level": "none",
            "risk_score": 0,
            "metadata": {"fria_id": fria_id, "submitted_by": payload.submitted_by},
        })
        db.commit()
        db.refresh(fria)
        return fria

    @staticmethod
    def review_fria(db: Session, tenant_id: str, fria_id: str, payload: FRIAReviewRequest) -> FRIARecord:
        fria = ObligationService.get_fria(db, tenant_id, fria_id)
        if fria.status != "in_review":
            raise HTTPException(status_code=409, detail="Only in-review FRIAs can be approved or rejected")
        if payload.outcome not in ("approved", "rejected"):
            raise HTTPException(status_code=422, detail="Outcome must be 'approved' or 'rejected'")
        fria.status = payload.outcome
        import datetime as _dt
        fria.approval_json = {
            **(fria.approval_json or {}),
            "reviewed_by": payload.reviewer_email,
            "reviewed_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "outcome": payload.outcome,
            "notes": payload.notes,
        }
        write_evidence_log(db, {
            "tenant_id": tenant_id,
            "ai_system_id": fria.ai_system_id,
            "evidence_domain": "governance_fria",
            "event_type": f"fria_{payload.outcome}",
            "request_id": f"req-{uuid.uuid4().hex[:8]}",
            "trace_id": f"trc-{uuid.uuid4().hex[:8]}",
            "decision": payload.outcome,
            "status": "success",
            "risk_level": "none",
            "risk_score": 0,
            "metadata": {"fria_id": fria_id, "reviewer": payload.reviewer_email},
        })
        db.commit()
        db.refresh(fria)
        return fria

    @staticmethod
    def export_fria_markdown(db: Session, tenant_id: str, fria_id: str) -> str:
        fria = ObligationService.get_fria(db, tenant_id, fria_id)
        s = fria.sections_json or {}
        approval = fria.approval_json or {}

        def section_block(title: str, key: str, fields: list[tuple[str, str]]) -> str:
            lines = [f"## {title}\n"]
            data = s.get(key, {})
            for field_key, label in fields:
                val = data.get(field_key, "_Not provided_")
                lines.append(f"**{label}**\n\n{val}\n")
            return "\n".join(lines)

        parts = [
            f"# Fundamental Rights Impact Assessment\n",
            f"**FRIA ID:** {fria.id}  \n**AI System ID:** {fria.ai_system_id}  \n**Status:** {fria.status}  \n**Completion:** {fria.completion_percent}%  \n**Created:** {fria.created_at.date()}  \n",
            "---\n",
            section_block("1. Intended Purpose", "intended_purpose", [
                ("system_description", "System Description"),
                ("deployment_context", "Deployment Context"),
                ("intended_users", "Intended Users"),
                ("geographic_scope", "Geographic Scope"),
            ]),
            section_block("2. Affected Persons", "affected_persons", [
                ("population_description", "Population Description"),
                ("vulnerable_groups", "Vulnerable Groups"),
                ("estimated_scale", "Estimated Scale"),
                ("interaction_type", "Interaction Type"),
            ]),
            section_block("3. Fundamental Rights Risks", "fundamental_rights_risks", [
                ("rights_at_risk", "Rights at Risk"),
                ("risk_descriptions", "Risk Descriptions"),
                ("severity_assessment", "Severity Assessment"),
                ("likelihood_assessment", "Likelihood Assessment"),
            ]),
            section_block("4. Mitigation Measures", "mitigation_measures", [
                ("technical_measures", "Technical Measures"),
                ("organizational_measures", "Organizational Measures"),
                ("human_oversight_measures", "Human Oversight Measures"),
                ("monitoring_approach", "Monitoring Approach"),
            ]),
            section_block("5. Human Oversight", "human_oversight", [
                ("oversight_roles", "Oversight Roles"),
                ("oversight_procedures", "Oversight Procedures"),
                ("override_capability", "Override Capability"),
                ("escalation_path", "Escalation Path"),
            ]),
            section_block("6. Residual Risk", "residual_risk", [
                ("remaining_risks", "Remaining Risks"),
                ("risk_acceptance_rationale", "Risk Acceptance Rationale"),
                ("review_schedule", "Review Schedule"),
                ("dpo_consulted", "DPO Consulted"),
            ]),
            "---\n",
            "## Legal Basis\n",
        ]
        for ref in (fria.legal_basis_json or []):
            parts.append(f"- **{ref.get('article', '')}**: {ref.get('title', '')} ({ref.get('source', '')})\n")

        if approval:
            parts += [
                "\n---\n",
                "## Approval Record\n",
                f"**Submitted by:** {approval.get('submitted_by', '_—_')}  \n",
                f"**Submitted at:** {approval.get('submitted_at', '_—_')}  \n",
                f"**Reviewed by:** {approval.get('reviewed_by', '_Pending_')}  \n",
                f"**Reviewed at:** {approval.get('reviewed_at', '_Pending_')}  \n",
                f"**Outcome:** {approval.get('outcome', '_Pending_')}  \n",
                f"**Notes:** {approval.get('notes') or '_None_'}  \n",
            ]

        return "\n".join(parts)

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
