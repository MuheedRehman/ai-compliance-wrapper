import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
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
)
from app.schemas import ReportCreate
from app.services.entitlement_service import check_entitlement
from app.services.hashing import hash_object
from app.services.regulatory_knowledge import article_refs, penalty_exposure_for_article

class ReportService:
    @staticmethod
    def _require_system(db: Session, tenant_id: str, ai_system_id: str | None) -> Optional[AiSystem]:
        if not ai_system_id:
            return None
        system = db.query(AiSystem).filter(AiSystem.tenant_id == tenant_id, AiSystem.id == ai_system_id).first()
        if not system:
            raise HTTPException(status_code=404, detail="AI system not found for tenant")
        return system

    @staticmethod
    def _require_feature(db: Session, tenant_id: str, feature_id: str | None) -> Optional[AiFeature]:
        if not feature_id:
            return None
        feature = db.query(AiFeature).filter(
            AiFeature.tenant_id == tenant_id,
            (AiFeature.id == feature_id) | (AiFeature.feature_id == feature_id),
        ).first()
        if not feature:
            raise HTTPException(status_code=404, detail="AI feature not found for tenant")
        return feature

    @staticmethod
    def list_reports(db: Session, tenant_id: str) -> List[ReportRecord]:
        return db.query(ReportRecord).filter(ReportRecord.tenant_id == tenant_id).order_by(ReportRecord.created_at.desc()).all()

    @staticmethod
    def get_report(db: Session, tenant_id: str, report_id: str) -> ReportRecord:
        report = db.query(ReportRecord).filter(ReportRecord.tenant_id == tenant_id, ReportRecord.id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report

    @staticmethod
    def generate_report(db: Session, tenant_id: str, payload: ReportCreate, *, commit: bool = True) -> ReportRecord:
        # Check entitlements (premium feature)
        if not check_entitlement(db, tenant_id, "report_generation"):
            raise HTTPException(status_code=403, detail="Report generation not entitled for this tenant")

        ai_system_id = payload.ai_system_id or None
        feature_id = payload.feature_id or None

        # Basic report shell
        report_id = f"rpt-{uuid.uuid4().hex[:8]}"
        title = payload.title or f"{payload.report_type.replace('_', ' ').title()} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Assemble findings and readiness
        findings = []
        source_refs = list(payload.source_refs or [])
        remediation_actions = []
        evidence_refs = []
        penalty_exposures = []
        readiness = "needs_attention"
        
        # System-level context
        system_name = "Generic Scope"
        system = ReportService._require_system(db, tenant_id, ai_system_id)
        if system:
            system_name = system.name
            source_refs.append({"type": "ai_system", "id": system.id, "name": system.name})

        # Feature-level context
        feature = ReportService._require_feature(db, tenant_id, feature_id)
        if feature:
            source_refs.append({"type": "ai_feature", "id": feature.id, "feature_id": feature.feature_id, "name": feature.name})

        # Data gathering logic based on report type
        if payload.report_type == "compliance_readiness_summary":
            # Check for FRIAs
            frias = db.query(FRIARecord).filter(FRIARecord.tenant_id == tenant_id)
            if ai_system_id:
                frias = frias.filter(FRIARecord.ai_system_id == ai_system_id)
            fria_list = frias.all()
            
            for f in fria_list:
                source_refs.append({"type": "fria", "id": f.id})
                if f.status == "completed":
                    findings.append({"title": f"FRIA Complete: {f.id}", "severity": "low", "description": "Mandated impact assessment has been finalized."})
                else:
                    findings.append({"title": f"FRIA Pending: {f.id}", "severity": "medium", "description": "Impact assessment is still in draft status."})
                    remediation_actions.append({"title": "Finalize FRIA", "description": f"Complete assessment for system {f.ai_system_id}"})

            # Check for Oversight
            oversights = db.query(OversightAssignment).filter(OversightAssignment.tenant_id == tenant_id)
            if ai_system_id:
                oversights = oversights.filter(OversightAssignment.ai_system_id == ai_system_id)
            ovs_list = oversights.all()
            
            if not ovs_list:
                findings.append({"title": "No Human Oversight", "severity": "high", "description": "No human oversight roles assigned for this scope."})
                remediation_actions.append({"title": "Assign Oversight", "description": "Assign technical or legal oversight roles."})
            else:
                findings.append({"title": f"{len(ovs_list)} Oversight Roles Assigned", "severity": "low", "description": "Human oversight mechanisms are in place."})
                for o in ovs_list: source_refs.append({"type": "oversight", "id": o.id})

            controls = db.query(ComplianceControl).filter(ComplianceControl.tenant_id == tenant_id)
            if ai_system_id:
                controls = controls.filter(ComplianceControl.ai_system_id == ai_system_id)
            control_list = controls.all()
            completed_statuses = {"completed", "signed_off"}
            completed_controls = [c for c in control_list if c.status in completed_statuses]
            incomplete_controls = [c for c in control_list if c.status not in completed_statuses]

            if not control_list:
                control_register_penalty = penalty_exposure_for_article("EU AI Act")
                findings.append({
                    "title": "Control Register Not Initialized",
                    "severity": "medium",
                    "description": "No compliance controls exist for this scope. Seed baseline controls before relying on readiness reporting.",
                    "penalty_exposure": control_register_penalty,
                })
                remediation_actions.append({
                    "title": "Seed EU AI Act Baseline Controls",
                    "description": "Create baseline controls for AI literacy, log retention, DPIA linkage, FRIA screening, post-market monitoring, and incident reporting.",
                    "penalty_exposure": control_register_penalty,
                })
                penalty_exposures.append(control_register_penalty)
            else:
                control_score = round((len(completed_controls) / len(control_list)) * 100)
                findings.append({
                    "title": f"Control Readiness {control_score}%",
                    "severity": "low" if control_score >= 80 else ("medium" if control_score >= 40 else "high"),
                    "description": f"{len(completed_controls)} of {len(control_list)} controls are completed or signed off."
                })
                for control in control_list:
                    penalty = ReportService._penalty_for_control(control)
                    penalty_exposures.append(penalty)
                    source_refs.append({
                        "type": "compliance_control",
                        "id": control.id,
                        "article": control.article,
                        "key": control.control_key,
                        "penalty_exposure": penalty,
                    })
                for control in incomplete_controls[:5]:
                    penalty = ReportService._penalty_for_control(control)
                    remediation_actions.append({
                        "title": f"Complete {control.article}: {control.title}",
                        "description": f"Assign owner and evidence for control `{control.control_key}`.",
                        "article": control.article,
                        "control_key": control.control_key,
                        "penalty_exposure": penalty,
                    })

            # Determine Readiness
            controls_ready = bool(control_list) and not incomplete_controls
            if fria_list and all(f.status == "completed" for f in fria_list) and ovs_list and controls_ready:
                readiness = "ready"
            elif fria_list or ovs_list or control_list:
                readiness = "partially_ready"

        elif payload.report_type == "incident_summary":
            incidents = db.query(IncidentRecord).filter(IncidentRecord.tenant_id == tenant_id)
            if ai_system_id:
                incidents = incidents.filter(IncidentRecord.ai_system_id == ai_system_id)
            inc_list = incidents.all()
            
            for inc in inc_list:
                source_refs.append({"type": "incident", "id": inc.id})
                findings.append({
                    "title": f"Incident {inc.id}: {inc.severity.upper()}",
                    "severity": inc.severity,
                    "description": inc.description[:200] + ("..." if len(inc.description) > 200 else "")
                })
                if inc.status != "resolved":
                    remediation_actions.append({"title": f"Resolve Incident {inc.id}", "description": "Conduct root cause analysis and close incident."})
            
            readiness = "ready" if all(inc.status == "resolved" for inc in inc_list) else "needs_attention"

        # Evidence gathering
        evidence_logs = db.query(EvidenceLog).filter(EvidenceLog.tenant_id == tenant_id)
        if ai_system_id:
            evidence_logs = evidence_logs.filter(EvidenceLog.ai_system_id == ai_system_id)
        logs = evidence_logs.limit(10).all() # Sample evidence
        for log in logs:
            evidence_refs.append({"id": log.event_id, "domain": log.evidence_domain, "type": log.event_type})

        # Build Report JSON
        legal_basis = article_refs("art_4", "art_26", "art_27", "art_72", "art_73")
        report_data = {
            "executive_summary": f"This {payload.report_type.replace('_', ' ')} evaluates the compliance posture of {system_name}.",
            "metadata": {
                "report_id": report_id,
                "tenant_id": tenant_id,
                "report_type": payload.report_type,
                "generated_at": datetime.now().isoformat(),
                "legal_disclaimer": "Automated compliance support output. Legal review is required before regulatory submission."
            },
            "findings": findings,
            "remediation_actions": remediation_actions,
            "evidence_references": evidence_refs,
            "legal_basis": legal_basis,
            "penalty_exposures": ReportService._dedupe_penalty_exposures(penalty_exposures),
            "readiness_summary": {
                "status": readiness,
                "rationale": "Generated based on available control, FRIA, oversight, incident, and evidence records."
            }
        }
        manifest = {
            "source_ref_count": len(source_refs),
            "evidence_ref_count": len(evidence_refs),
            "report_hash": hash_object(report_data),
            "artifact_formats": ["json", "markdown"],
        }

        # Persist
        report = ReportRecord(
            id=report_id,
            tenant_id=tenant_id,
            report_type=payload.report_type,
            title=title,
            status="completed",
            report_json=report_data,
            source_refs_json=source_refs,
            artifact_metadata={
                "json": f"{report_id}.json",
                "markdown": f"{report_id}.md"
            },
            legal_basis_json=legal_basis,
            generation_manifest_json=manifest,
            ai_system_id=ai_system_id,
            feature_id=feature_id
        )
        db.add(report)
        db.flush()
        if commit:
            db.commit()
            db.refresh(report)
        return report

    @staticmethod
    def get_artifact(report: ReportRecord, artifact_name: str) -> str:
        if artifact_name.endswith(".json"):
            return json.dumps(report.report_json, indent=2)
        elif artifact_name.endswith(".md"):
            return ReportService._generate_markdown(report)
        else:
            raise HTTPException(status_code=404, detail="Artifact not found")

    @staticmethod
    def _generate_markdown(report: ReportRecord) -> str:
        data = report.report_json
        md = f"# {report.title}\n\n"
        md += f"**Report ID:** `{report.id}`  \n"
        md += f"**Generated At:** {data['metadata']['generated_at']}  \n"
        md += f"**Readiness:** {data['readiness_summary']['status'].upper()}\n\n"
        
        md += "## Executive Summary\n"
        md += f"{data['executive_summary']}\n\n"
        
        md += "## Findings\n"
        if not data['findings']:
            md += "No findings recorded.\n"
        for f in data['findings']:
            md += f"### {f['title']} ({f['severity'].upper()})\n"
            md += f"{f['description']}\n\n"
            
        md += "## Remediation Actions\n"
        if not data['remediation_actions']:
            md += "No immediate remediation actions required.\n"
        for a in data['remediation_actions']:
            md += f"- **{a['title']}**: {a['description']}\n"
        md += "\n"

        if data.get("legal_basis"):
            md += "## Legal Basis\n"
            for ref in data["legal_basis"]:
                md += f"- **{ref['article']}**: {ref['title']}\n"
            md += "\n"

        if data.get("penalty_exposures"):
            md += "## Penalty Exposure\n"
            for penalty in data["penalty_exposures"]:
                md += f"- **{penalty['enforcement_article']}**: {penalty['maximum_text']} {penalty['notes']}\n"
            md += "\n"
        
        md += "## Evidence Traceability\n"
        for e in data['evidence_references']:
            md += f"- `{e['id']}`: {e['domain']} / {e['type']}\n"
            
        md += "\n---\n*This report is generated automatically by the EU AI Act Compliance Platform. It does not constitute legal advice.*"
        return md

    @staticmethod
    def _penalty_for_control(control: ComplianceControl) -> dict[str, Any]:
        details = control.details_json or {}
        penalty = details.get("penalty_exposure")
        if penalty:
            return penalty
        return penalty_exposure_for_article(control.article)

    @staticmethod
    def _dedupe_penalty_exposures(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for item in items:
            band_id = item.get("band_id")
            if not band_id or band_id in seen:
                continue
            seen.add(band_id)
            deduped.append(item)
        return deduped
