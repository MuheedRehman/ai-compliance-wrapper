import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import IntakeAssessment
from app.schemas import IntakeCreate
from app.services.compliance_control_service import ComplianceControlService
from app.services.regulatory_knowledge import build_obligation_graph, explain_obligations, legal_basis_for_classification
from typing import Any, Dict, List

class ClassificationService:
    @staticmethod
    def _run_classification_logic(answers: Dict[str, Any]) -> Dict[str, str]:
        """
        Deterministic classification logic for EU AI Act.
        """
        # 1. Determine Actor Role
        # Precedence: Provider > Deployer > Other
        # Although the UI restricts this to a single selection, the backend
        # remains deterministic if both flags are somehow passed.
        is_developer = answers.get("is_developer", False)
        is_deployer = answers.get("is_deployer", False)
        
        if is_developer:
            actor_role = "Provider"
        elif is_deployer:
            actor_role = "Deployer"
        else:
            actor_role = "Importer/Distributor"
            
        # 2. Determine System Classification
        is_prohibited = answers.get("is_prohibited_use", False)
        is_high_risk = answers.get("is_high_risk_annex_iii", False) or answers.get("is_safety_component", False)
        is_limited_risk = answers.get("has_transparency_obligation", False)
        is_gpai = answers.get("is_gpai", False)
        
        rationale_parts = []
        
        if is_prohibited:
            system_classification = "Prohibited AI System"
            obligation_path = "CEASE_AND_DESIST"
            rationale_parts.append("The system uses prohibited AI practices (Art 5).")
        elif is_high_risk:
            system_classification = "High-Risk AI System"
            annex_matches = answers.get("annex_iii_matches") or []
            if annex_matches:
                annex_labels = ", ".join(
                    f"{match.get('annex_ref')}: {match.get('subcategory')}"
                    for match in annex_matches[:3]
                )
                rationale_parts.append(f"Annex III category evidence detected: {annex_labels}.")
            if actor_role == "Provider":
                obligation_path = "FULL_COMPLIANCE_ART_16"
                rationale_parts.append("System is high-risk; provider must follow Art 16 obligations (QMS, Technical Doc, Conformity Assessment).")
            elif actor_role == "Deployer":
                obligation_path = "OPERATIONAL_GOVERNANCE_ART_26"
                rationale_parts.append("System is high-risk; deployer must follow Article 26 obligations (instructions for use, competent human oversight, monitoring, and log retention).")
            else:
                # Importer / Distributor
                obligation_path = "IMPORTER_DISTRIBUTOR_REVIEW_REQUIRED"
                rationale_parts.append("System is high-risk; importers and distributors must verify value-chain compliance and supporting documentation. Separate review required under this model.")
        elif is_gpai:
            system_classification = "General Purpose AI (GPAI)"
            obligation_path = "GPAI_COMPLIANCE_ART_51_53"
            rationale_parts.append("System is a GPAI model; specific transparency and technical documentation required.")
        elif is_limited_risk:
            system_classification = "Limited Risk AI System"
            obligation_path = "TRANSPARENCY_ART_50"
            rationale_parts.append("System carries transparency risks (e.g. chatbots, deepfakes) requiring Article 50 disclosure to users.")
        else:
            system_classification = "Minimal Risk AI System"
            obligation_path = "VOLUNTARY_CODE_OF_CONDUCT"
            rationale_parts.append("System falls outside specific high/limited risk categories. Voluntary codes of conduct encouraged.")
            
        obligation_graph = build_obligation_graph(actor_role, system_classification, answers)
        legal_basis = legal_basis_for_classification(system_classification, answers, actor_role)

        return {
            "actor_role": actor_role,
            "system_classification": system_classification,
            "obligation_path": obligation_path,
            "obligation_graph": obligation_graph,
            "legal_basis": legal_basis,
            "annex_iii_matches": answers.get("annex_iii_matches", []),
            "evidence_requirements": [
                {
                    "key": item["key"],
                    "dimension_id": item.get("dimension_id", item["key"]),
                    "article": item["article"],
                    "evidence_domain": item["evidence_domain"],
                    "status": item["status"],
                    "required_evidence": item.get("required_evidence", []),
                }
                for item in obligation_graph
            ],
            "rationale": " ".join(rationale_parts)
        }

    @classmethod
    def create_intake(cls, db: Session, tenant_id: str, payload: IntakeCreate) -> IntakeAssessment:
        results = cls._run_classification_logic(payload.answers)
        
        intake = IntakeAssessment(
            id=f"intake-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            title=payload.title,
            answers_json=payload.answers,
            actor_role=results["actor_role"],
            system_classification=results["system_classification"],
            obligation_path=results["obligation_path"],
            obligation_graph_json=results["obligation_graph"],
            legal_basis_json=results["legal_basis"],
            evidence_requirements_json=results["evidence_requirements"],
            rationale=results["rationale"]
        )
        
        db.add(intake)
        db.commit()
        db.refresh(intake)
        return intake

    @staticmethod
    def list_intakes(db: Session, tenant_id: str) -> List[IntakeAssessment]:
        return db.query(IntakeAssessment).filter(IntakeAssessment.tenant_id == tenant_id).order_by(IntakeAssessment.created_at.desc()).all()

    @staticmethod
    def get_intake(db: Session, tenant_id: str, intake_id: str) -> IntakeAssessment:
        intake = db.query(IntakeAssessment).filter(
            IntakeAssessment.tenant_id == tenant_id,
            IntakeAssessment.id == intake_id
        ).first()
        
        if not intake:
            raise HTTPException(status_code=404, detail="Intake assessment not found")
            
        return intake

    @classmethod
    def explain_intake(cls, db: Session, tenant_id: str, intake_id: str) -> dict:
        intake = cls.get_intake(db, tenant_id, intake_id)
        return explain_obligations(
            intake.actor_role,
            intake.system_classification,
            intake.obligation_path,
            intake.answers_json or {},
        )

    @classmethod
    def materialize_control_plan(cls, db: Session, tenant_id: str, intake_id: str, ai_system_id: str | None = None):
        intake = cls.get_intake(db, tenant_id, intake_id)
        return ComplianceControlService.seed_from_obligation_graph(
            db,
            tenant_id,
            intake.obligation_graph_json or [],
            intake_id=intake.id,
            obligation_path=intake.obligation_path,
            ai_system_id=ai_system_id,
        )
