import io
import json
import uuid
import zipfile
from datetime import datetime
from typing import List, Optional, Dict, Any
from fpdf import FPDF
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import (
    AiFeature,
    AiSystem,
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
        scanner_audit_pack = None
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

            scanner_audit_pack = ReportService._build_scanner_audit_pack(db, tenant_id, source_refs, ai_system_id)
            if scanner_audit_pack:
                findings.extend(scanner_audit_pack["findings"])
                remediation_actions.extend(scanner_audit_pack["remediation_actions"])
                evidence_refs.extend(scanner_audit_pack["evidence_references"])
                penalty_exposures.extend(scanner_audit_pack["penalty_exposures"])
                if scanner_audit_pack["high_or_medium_gap_count"]:
                    readiness = "needs_attention" if readiness == "ready" else readiness

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

        elif payload.report_type == "ai_system_factsheet":
            if not system:
                raise HTTPException(status_code=400, detail="ai_system_id is required for ai_system_factsheet")

            # FRIA status
            frias = db.query(FRIARecord).filter(
                FRIARecord.tenant_id == tenant_id,
                FRIARecord.ai_system_id == ai_system_id,
            ).order_by(FRIARecord.updated_at.desc()).all()
            latest_fria = frias[0] if frias else None

            # Compliance controls
            controls = db.query(ComplianceControl).filter(
                ComplianceControl.tenant_id == tenant_id,
                ComplianceControl.ai_system_id == ai_system_id,
            ).all()
            completed_statuses = {"completed", "signed_off"}
            control_score = (
                round(sum(1 for c in controls if c.status in completed_statuses) / len(controls) * 100)
                if controls else 0
            )

            # Oversight
            oversights = db.query(OversightAssignment).filter(
                OversightAssignment.tenant_id == tenant_id,
                OversightAssignment.ai_system_id == ai_system_id,
            ).all()

            # Open incidents
            incidents = db.query(IncidentRecord).filter(
                IncidentRecord.tenant_id == tenant_id,
                IncidentRecord.ai_system_id == ai_system_id,
                IncidentRecord.status != "resolved",
            ).all()

            # Latest scan
            latest_scan = db.query(WebsiteScan).filter(
                WebsiteScan.tenant_id == tenant_id,
                WebsiteScan.ai_system_id == ai_system_id,
            ).order_by(WebsiteScan.created_at.desc()).first()

            report_data["factsheet"] = {
                "system": {
                    "id": system.id,
                    "name": system.name,
                    "risk_level": getattr(system, "risk_level", None),
                    "lifecycle_status": getattr(system, "lifecycle_status", None),
                    "annex_iii_category": getattr(system, "annex_iii_category", None),
                },
                "fria": {
                    "status": latest_fria.status if latest_fria else "not_started",
                    "completion_percent": latest_fria.completion_percent if latest_fria else 0,
                    "fria_id": latest_fria.id if latest_fria else None,
                    "total_count": len(frias),
                },
                "compliance": {
                    "control_count": len(controls),
                    "completion_score": control_score,
                },
                "oversight": {
                    "assignment_count": len(oversights),
                    "roles": [o.role_type for o in oversights] if oversights else [],
                },
                "incidents": {
                    "open_count": len(incidents),
                    "ids": [i.id for i in incidents[:5]],
                },
                "scanner": {
                    "last_scan_id": latest_scan.id if latest_scan else None,
                    "last_scan_url": latest_scan.normalized_url if latest_scan else None,
                    "confidence_score": latest_scan.confidence_score if latest_scan else None,
                } if latest_scan else None,
            }

            # Findings driven from factsheet data
            if not latest_fria:
                findings.append({"title": "No FRIA recorded", "severity": "high", "description": "An EU AI Act Article 27 impact assessment has not been started."})
                remediation_actions.append({"title": "Start FRIA", "description": "Create a Fundamental Rights Impact Assessment for this system."})
            elif latest_fria.status not in ("approved", "completed"):
                findings.append({"title": f"FRIA {latest_fria.completion_percent}% complete", "severity": "medium", "description": f"The FRIA is in '{latest_fria.status}' state."})

            if control_score < 80:
                findings.append({"title": f"Control score {control_score}%", "severity": "medium" if control_score >= 40 else "high", "description": f"Only {control_score}% of compliance controls are complete."})

            if not oversights:
                findings.append({"title": "No human oversight", "severity": "high", "description": "No oversight roles are assigned to this system."})

            for inc in incidents[:3]:
                findings.append({"title": f"Open incident: {inc.severity.upper()}", "severity": inc.severity, "description": inc.description[:150]})

            readiness = (
                "ready" if (latest_fria and latest_fria.status in ("approved", "completed") and oversights and control_score >= 80 and not incidents)
                else ("partially_ready" if (latest_fria or oversights or controls) else "needs_attention")
            )

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
        if scanner_audit_pack:
            report_data["scanner_audit_pack"] = scanner_audit_pack
        manifest = {
            "source_ref_count": len(source_refs),
            "evidence_ref_count": len(evidence_refs),
            "report_hash": hash_object(report_data),
            "artifact_formats": ["json", "markdown", "pdf"],
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
                "markdown": f"{report_id}.md",
                "pdf": f"{report_id}.pdf",
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
    def _build_scanner_audit_pack(
        db: Session,
        tenant_id: str,
        source_refs: list[dict[str, Any]],
        ai_system_id: str | None,
    ) -> dict[str, Any] | None:
        scan_ids = [
            ref.get("id")
            for ref in source_refs
            if ref.get("type") == "website_scan" and ref.get("id")
        ]
        query = db.query(WebsiteScan).filter(WebsiteScan.tenant_id == tenant_id)
        if scan_ids:
            scans = query.filter(WebsiteScan.id.in_(scan_ids)).all()
        elif ai_system_id:
            scans = query.filter(WebsiteScan.ai_system_id == ai_system_id).order_by(WebsiteScan.created_at.desc()).limit(3).all()
        else:
            scans = []
        if not scans:
            return None

        findings: list[dict[str, Any]] = []
        remediation_actions: list[dict[str, Any]] = []
        evidence_references: list[dict[str, Any]] = []
        penalty_exposures: list[dict[str, Any]] = []
        scans_summary: list[dict[str, Any]] = []
        public_sources: list[dict[str, Any]] = []
        found_topics: list[dict[str, Any]] = []
        missing_topics: set[str] = set()
        high_or_medium_gap_count = 0

        for scan in scans:
            classification = scan.classification_json or {}
            profile = classification.get("public_evidence_profile") or {}
            topics = profile.get("topics") or []
            gaps = scan.gap_findings_json or []
            annex_matches = classification.get("annex_iii_matches") or []

            for topic in topics:
                found_topics.append({
                    "scan_id": scan.id,
                    "topic": topic.get("topic"),
                    "label": topic.get("label"),
                    "source_url": topic.get("source_url"),
                    "excerpt": topic.get("excerpt"),
                    "dimension_id": topic.get("dimension_id"),
                    "article": topic.get("article"),
                    "evidence_domain": topic.get("evidence_domain"),
                })
                evidence_references.append({
                    "id": f"{scan.id}:{topic.get('topic')}",
                    "domain": topic.get("evidence_domain") or "website_scan",
                    "type": "public_evidence_topic",
                    "source_url": topic.get("source_url"),
                })

            for topic in profile.get("missing_topics") or []:
                missing_topics.add(topic)

            for gap in gaps:
                if gap.get("severity") in {"high", "medium"}:
                    high_or_medium_gap_count += 1
                    findings.append({
                        "title": f"Scanner gap: {gap.get('title', 'Public-page evidence gap')}",
                        "severity": gap.get("severity", "medium"),
                        "description": gap.get("detail", "The website scanner identified a public-page evidence gap."),
                        "article": gap.get("article"),
                        "dimension_id": gap.get("dimension_id"),
                        "penalty_exposure": gap.get("penalty_exposure"),
                    })
                    remediation_actions.append({
                        "title": f"Resolve scanner gap: {gap.get('title', 'Public-page evidence gap')}",
                        "description": gap.get("detail", "Add or attach evidence that closes this scanner finding."),
                        "article": gap.get("article"),
                        "dimension_id": gap.get("dimension_id"),
                        "penalty_exposure": gap.get("penalty_exposure"),
                    })
                    if gap.get("penalty_exposure"):
                        penalty_exposures.append(gap["penalty_exposure"])

            for page in scan.source_pages_json or []:
                public_sources.append({
                    "scan_id": scan.id,
                    "url": page.get("url"),
                    "title": page.get("title"),
                    "text_excerpt": page.get("text_excerpt"),
                    "evidence_topics": page.get("evidence_topics", []),
                })

            scans_summary.append({
                "scan_id": scan.id,
                "url": scan.normalized_url,
                "title": scan.title,
                "status": scan.status,
                "confidence_score": scan.confidence_score,
                "risk_level": classification.get("risk_level"),
                "classification": classification.get("classification"),
                "selected_actor_role": classification.get("selected_actor_role") or classification.get("canonical_actor_role"),
                "coverage_score": profile.get("coverage_score", 0),
                "coverage": profile.get("coverage", {}),
                "gap_count": len(gaps),
                "high_or_medium_gap_count": sum(1 for gap in gaps if gap.get("severity") in {"high", "medium"}),
                "annex_iii_matches": annex_matches,
            })

        coverage_scores = [scan["coverage_score"] for scan in scans_summary if scan.get("coverage_score") is not None]
        return {
            "summary": {
                "scan_count": len(scans_summary),
                "average_public_evidence_coverage": round(sum(coverage_scores) / len(coverage_scores)) if coverage_scores else 0,
                "found_topic_count": len(found_topics),
                "missing_topic_count": len(missing_topics),
                "high_or_medium_gap_count": high_or_medium_gap_count,
            },
            "scans": scans_summary,
            "found_topics": found_topics,
            "missing_topics": sorted(missing_topics),
            "public_sources": public_sources,
            "findings": findings,
            "remediation_actions": remediation_actions,
            "evidence_references": evidence_references,
            "penalty_exposures": ReportService._dedupe_penalty_exposures(penalty_exposures),
            "high_or_medium_gap_count": high_or_medium_gap_count,
        }

    @staticmethod
    def get_artifact(report: ReportRecord, artifact_name: str) -> str | bytes:
        if artifact_name.endswith(".json"):
            return json.dumps(report.report_json, indent=2)
        elif artifact_name.endswith(".md"):
            return ReportService._generate_markdown(report)
        elif artifact_name.endswith(".pdf"):
            return ReportService._generate_pdf(report)
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

        if data.get("scanner_audit_pack"):
            pack = data["scanner_audit_pack"]
            summary = pack.get("summary", {})
            md += "## Website Scanner Audit Pack\n"
            md += f"- Scans reviewed: {summary.get('scan_count', 0)}\n"
            md += f"- Public evidence coverage: {summary.get('average_public_evidence_coverage', 0)}%\n"
            md += f"- Found evidence topics: {summary.get('found_topic_count', 0)}\n"
            md += f"- Missing evidence topics: {summary.get('missing_topic_count', 0)}\n"
            md += f"- High/medium scanner gaps: {summary.get('high_or_medium_gap_count', 0)}\n\n"
            if pack.get("missing_topics"):
                md += "### Missing Public Evidence Topics\n"
                for topic in pack["missing_topics"]:
                    md += f"- {topic}\n"
                md += "\n"
            if pack.get("found_topics"):
                md += "### Found Public Evidence Topics\n"
                for topic in pack["found_topics"][:10]:
                    md += f"- **{topic.get('label')}** ({topic.get('article')}): {topic.get('source_url')}\n"
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

    # ------------------------------------------------------------------
    # PDF generation (fpdf2)
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_text(text: str, max_len: int = 0) -> str:
        """Coerce text to Latin-1 safe (fpdf2 core fonts are Latin-1 only)."""
        sanitized = (text or "").encode("latin-1", errors="replace").decode("latin-1")
        return sanitized[:max_len] if max_len else sanitized

    @staticmethod
    def _generate_pdf(report: ReportRecord) -> bytes:
        data = report.report_json or {}
        findings = data.get("findings", [])
        remediation_actions = data.get("remediation_actions", [])
        penalty_exposures = data.get("penalty_exposures", [])
        readiness = data.get("readiness_summary", {}).get("status", "unknown")
        factsheet = data.get("factsheet")
        s = ReportService._safe_text

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_margins(20, 15, 20)
        pdf.add_page()

        # ---- Header bar ----
        pdf.set_fill_color(45, 45, 55)
        pdf.rect(0, 0, 210, 28, "F")
        pdf.set_xy(20, 7)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, "EU AI Act Compliance Platform", ln=True)
        pdf.set_xy(20, 16)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(160, 160, 180)
        pdf.cell(0, 6, f"CONFIDENTIAL - {report.report_type.replace('_', ' ').upper()}", ln=True)
        pdf.set_text_color(30, 30, 40)

        # ---- Title block ----
        pdf.set_xy(20, 34)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(20, 20, 30)
        pdf.multi_cell(170, 9, s(report.title))
        pdf.ln(2)

        # Readiness badge
        READINESS_COLORS = {
            "ready": (16, 185, 129),
            "partially_ready": (245, 158, 11),
            "needs_attention": (239, 68, 68),
        }
        badge_r, badge_g, badge_b = READINESS_COLORS.get(readiness, (100, 100, 120))
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(badge_r, badge_g, badge_b)
        pdf.cell(0, 6, f"Readiness: {readiness.replace('_', ' ').upper()}", ln=True)
        pdf.ln(2)

        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(120, 120, 140)
        meta = data.get("metadata", {})
        pdf.cell(0, 5, f"Report ID: {report.id}  |  Generated: {meta.get('generated_at', '')[:19].replace('T', ' ')} UTC", ln=True)
        pdf.ln(4)

        pdf.set_draw_color(220, 220, 230)
        pdf.set_line_width(0.3)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)

        # ---- Factsheet summary card (if present) ----
        if factsheet:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(40, 40, 60)
            pdf.cell(0, 7, "AI System Factsheet", ln=True)
            pdf.ln(1)
            sys_info = factsheet.get("system", {})
            fria_info = factsheet.get("fria", {})
            ctrl_info = factsheet.get("compliance", {})
            ovs_info = factsheet.get("oversight", {})
            inc_info = factsheet.get("incidents", {})
            cards = [
                ("System", sys_info.get("name", "—")),
                ("Risk Level", sys_info.get("risk_level") or "—"),
                ("FRIA Status", fria_info.get("status", "—")),
                ("FRIA Progress", f"{fria_info.get('completion_percent', 0)}%"),
                ("Controls Done", f"{ctrl_info.get('completion_score', 0)}%"),
                ("Oversight Roles", str(ovs_info.get("assignment_count", 0))),
                ("Open Incidents", str(inc_info.get("open_count", 0))),
            ]
            col_w = 80
            row_h = 8
            for i, (label, value) in enumerate(cards):
                x = 20 + (i % 2) * col_w
                y = pdf.get_y() if i % 2 == 0 else pdf.get_y() - row_h
                if i % 2 == 0 and i > 0:
                    pdf.ln(0)
                pdf.set_xy(x, pdf.get_y() if i % 2 == 0 else y)
                pdf.set_fill_color(248, 248, 252)
                pdf.rect(x, pdf.get_y(), col_w - 3, row_h, "FD")
                pdf.set_font("Helvetica", "", 7)
                pdf.set_text_color(110, 110, 130)
                pdf.set_xy(x + 2, pdf.get_y() + 1)
                pdf.cell(col_w - 7, 3, label.upper(), ln=False)
                pdf.set_xy(x + 2, pdf.get_y() + 3)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(30, 30, 50)
                pdf.cell(col_w - 7, 3, s(str(value), 25), ln=True if i % 2 == 1 or i == len(cards) - 1 else False)
                if i % 2 == 0:
                    pdf.set_xy(20 + col_w, y if i > 0 else pdf.get_y() - row_h)
            pdf.ln(6)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(5)

        # ---- Executive summary ----
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(40, 40, 60)
        pdf.cell(0, 7, "Executive Summary", ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 80)
        pdf.multi_cell(170, 5, s(data.get("executive_summary", "")))
        pdf.ln(4)

        # ---- Findings ----
        if findings:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(40, 40, 60)
            pdf.cell(0, 7, f"Key Findings ({len(findings)})", ln=True)
            pdf.ln(1)
            SEV_COLORS = {"high": (239, 68, 68), "medium": (245, 158, 11), "low": (16, 185, 129)}
            for f in findings:
                sev = f.get("severity", "low")
                cr, cg, cb = SEV_COLORS.get(sev, (100, 100, 120))
                pdf.set_fill_color(cr, cg, cb)
                pdf.rect(20, pdf.get_y(), 2, 12, "F")
                pdf.set_x(24)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(30, 30, 50)
                pdf.cell(150, 5, s(f.get("title", ""), 80), ln=True)
                pdf.set_x(24)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(80, 80, 100)
                pdf.multi_cell(166, 4, s(f.get("description", ""), 200))
                pdf.ln(2)

        # ---- Remediation Actions ----
        if remediation_actions:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(40, 40, 60)
            pdf.cell(0, 7, "Required Actions", ln=True)
            pdf.ln(1)
            for i, action in enumerate(remediation_actions, 1):
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(80, 80, 200)
                pdf.cell(8, 5, f"{i}.", ln=False)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(30, 30, 50)
                pdf.cell(0, 5, s(action.get("title", ""), 80), ln=True)
                pdf.set_x(28)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(80, 80, 100)
                pdf.multi_cell(162, 4, s(action.get("description", ""), 200))
                pdf.ln(2)

        # ---- Penalty Exposure ----
        if penalty_exposures:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(40, 40, 60)
            pdf.cell(0, 7, "Fine Exposure", ln=True)
            pdf.ln(1)
            for p in penalty_exposures:
                pdf.set_fill_color(255, 245, 245)
                pdf.set_draw_color(239, 68, 68)
                pdf.set_line_width(0.2)
                x, y = pdf.get_x(), pdf.get_y()
                pdf.rect(20, y, 170, 12, "FD")
                pdf.set_xy(23, y + 1)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(180, 30, 30)
                pdf.cell(170, 4, s(p.get("enforcement_article", "")), ln=True)
                pdf.set_x(23)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(80, 40, 40)
                note = s(p.get("maximum_text") or p.get("notes") or "", 100)
                pdf.cell(167, 4, note, ln=True)
                pdf.ln(2)

        # ---- Footer ----
        pdf.set_y(-20)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(150, 150, 160)
        pdf.cell(0, 4, "Generated by the EU AI Act Compliance Platform. This report does not constitute legal advice.", align="C", ln=True)

        return bytes(pdf.output())

    # ------------------------------------------------------------------
    # Evidence bundle (ZIP)
    # ------------------------------------------------------------------

    @staticmethod
    def get_bundle(db: Session, tenant_id: str, report_id: str) -> bytes:
        report = ReportService.get_report(db, tenant_id, report_id)
        buf = io.BytesIO()
        prefix = report.id

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Core report artifacts
            zf.writestr(f"{prefix}/report.json", json.dumps(report.report_json, indent=2))
            zf.writestr(f"{prefix}/report.md", ReportService._generate_markdown(report))
            zf.writestr(f"{prefix}/report.pdf", ReportService._generate_pdf(report))

            # Source references index
            zf.writestr(f"{prefix}/sources.json", json.dumps(report.source_refs_json or [], indent=2))

            # Evidence items for the report's AI system (if any)
            ai_system_id = report.ai_system_id
            if ai_system_id:
                items = db.query(EvidenceItem).filter(
                    EvidenceItem.tenant_id == tenant_id,
                    EvidenceItem.ai_system_id == ai_system_id,
                ).all()
                evidence_export = [
                    {
                        "id": e.id,
                        "title": e.title,
                        "control_domain": e.control_domain,
                        "status": e.status,
                        "collected_at": e.collected_at.isoformat() if e.collected_at else None,
                        "owner_email": e.owner_email,
                        "notes": e.notes,
                        "artifact_count": len(e.artifacts) if hasattr(e, "artifacts") else 0,
                    }
                    for e in items
                ]
                zf.writestr(f"{prefix}/evidence/evidence_items.json", json.dumps(evidence_export, indent=2))

                # FRIA sections for the system
                frias = db.query(FRIARecord).filter(
                    FRIARecord.tenant_id == tenant_id,
                    FRIARecord.ai_system_id == ai_system_id,
                ).all()
                if frias:
                    fria_export = [
                        {
                            "id": f.id,
                            "status": f.status,
                            "completion_percent": f.completion_percent,
                            "sections": f.sections_json,
                            "approval": f.approval_json,
                        }
                        for f in frias
                    ]
                    zf.writestr(f"{prefix}/evidence/fria_records.json", json.dumps(fria_export, indent=2))

                # Incident records
                incidents = db.query(IncidentRecord).filter(
                    IncidentRecord.tenant_id == tenant_id,
                    IncidentRecord.ai_system_id == ai_system_id,
                ).all()
                if incidents:
                    inc_export = [
                        {"id": i.id, "severity": i.severity, "status": i.status, "description": i.description}
                        for i in incidents
                    ]
                    zf.writestr(f"{prefix}/evidence/incidents.json", json.dumps(inc_export, indent=2))

            # Manifest
            manifest = {
                "bundle_created_at": datetime.now().isoformat(),
                "report_id": report.id,
                "report_type": report.report_type,
                "tenant_id": tenant_id,
                "ai_system_id": ai_system_id,
                "files": [
                    f"{prefix}/report.json",
                    f"{prefix}/report.md",
                    f"{prefix}/report.pdf",
                    f"{prefix}/sources.json",
                ],
            }
            zf.writestr(f"{prefix}/manifest.json", json.dumps(manifest, indent=2))

        buf.seek(0)
        return buf.read()
