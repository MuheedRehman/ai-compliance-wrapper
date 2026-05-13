import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AiSystem, ComplianceControl
from app.schemas import ComplianceControlCreate, ComplianceControlUpdate


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


class ComplianceControlService:
    @staticmethod
    def _require_system(db: Session, tenant_id: str, ai_system_id: Optional[str]) -> None:
        if not ai_system_id:
            return
        exists = db.query(AiSystem.id).filter(AiSystem.tenant_id == tenant_id, AiSystem.id == ai_system_id).first()
        if not exists:
            raise HTTPException(status_code=404, detail="AI system not found for tenant")

    @staticmethod
    def list_controls(db: Session, tenant_id: str, ai_system_id: Optional[str] = None) -> List[ComplianceControl]:
        query = db.query(ComplianceControl).filter(ComplianceControl.tenant_id == tenant_id)
        if ai_system_id:
            query = query.filter(ComplianceControl.ai_system_id == ai_system_id)
        return query.order_by(ComplianceControl.article.asc(), ComplianceControl.control_key.asc()).all()

    @staticmethod
    def create_control(db: Session, tenant_id: str, payload: ComplianceControlCreate) -> ComplianceControl:
        ComplianceControlService._require_system(db, tenant_id, payload.ai_system_id)
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
            details_json=payload.details_json,
        )
        db.add(control)
        db.commit()
        db.refresh(control)
        return control

    @staticmethod
    def update_control(db: Session, tenant_id: str, control_id: str, payload: ComplianceControlUpdate) -> ComplianceControl:
        control = db.query(ComplianceControl).filter(
            ComplianceControl.tenant_id == tenant_id,
            ComplianceControl.id == control_id,
        ).first()
        if not control:
            raise HTTPException(status_code=404, detail="Compliance control not found")

        if payload.owner_email is not None:
            control.owner_email = payload.owner_email
        if payload.status is not None:
            control.status = payload.status
        if payload.due_at is not None:
            control.due_at = payload.due_at
        if payload.details_json is not None:
            control.details_json = payload.details_json

        db.commit()
        db.refresh(control)
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
                details_json={"source": "baseline_eu_ai_act_controls"},
                **item,
            )
            db.add(control)
            created.append(control)
        db.commit()
        for control in created:
            db.refresh(control)
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
                },
            )
            db.add(control)
            created.append(control)

        db.commit()
        for control in created:
            db.refresh(control)
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


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _status_from_obligation(status: Optional[str]) -> str:
    if status in {"blocking", "review_required"}:
        return "blocked"
    return "not_started"
