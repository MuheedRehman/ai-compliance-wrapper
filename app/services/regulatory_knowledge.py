from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


AI_ACT_SOURCE = "Regulation (EU) 2024/1689"
AI_ACT_SERVICE_DESK_BASE = "https://ai-act-service-desk.ec.europa.eu/en/ai-act"


REGULATORY_ARTICLES: dict[str, dict[str, str]] = {
    "art_4": {
        "article": "Article 4",
        "title": "AI literacy",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-4",
    },
    "art_5": {
        "article": "Article 5",
        "title": "Prohibited AI practices",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-5",
    },
    "art_6_annex_iii": {
        "article": "Article 6 and Annex III",
        "title": "Classification rules for high-risk AI systems",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-6",
    },
    "art_16": {
        "article": "Article 16",
        "title": "Provider obligations for high-risk AI systems",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-16",
    },
    "art_26": {
        "article": "Article 26",
        "title": "Deployer obligations for high-risk AI systems",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-26",
    },
    "art_27": {
        "article": "Article 27",
        "title": "Fundamental rights impact assessment",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-27",
    },
    "art_50": {
        "article": "Article 50",
        "title": "Transparency obligations",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-50",
    },
    "art_72": {
        "article": "Article 72",
        "title": "Post-market monitoring",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-72",
    },
    "art_73": {
        "article": "Article 73",
        "title": "Serious incident reporting",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-73",
    },
}


def article_refs(*keys: str) -> list[dict[str, str]]:
    return [{"source": AI_ACT_SOURCE, **REGULATORY_ARTICLES[key]} for key in keys]


def build_obligation_graph(actor_role: str, classification: str, answers: dict[str, Any]) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = [
        {
            "key": "ai_literacy",
            "article": "Article 4",
            "owner_role": actor_role,
            "status": "required",
            "evidence_domain": "ai_literacy",
            "summary": "Maintain role-appropriate AI literacy for staff and operators.",
        }
    ]

    if classification == "Prohibited AI System":
        obligations.append({
            "key": "prohibited_use_review",
            "article": "Article 5",
            "owner_role": actor_role,
            "status": "blocking",
            "evidence_domain": "classification",
            "summary": "Cease or redesign the prohibited use before deployment.",
        })
        return obligations

    if classification == "High-Risk AI System":
        if actor_role == "Provider":
            obligations.extend([
                {
                    "key": "provider_high_risk_controls",
                    "article": "Article 16",
                    "owner_role": "Provider",
                    "status": "required",
                    "evidence_domain": "provider_controls",
                    "summary": "Implement provider obligations including QMS, technical documentation, conformity assessment, and declaration of conformity.",
                },
                {
                    "key": "post_market_monitoring_plan",
                    "article": "Article 72",
                    "owner_role": "Provider",
                    "status": "required",
                    "evidence_domain": "post_market_monitoring",
                    "summary": "Establish and document post-market monitoring for the high-risk AI system.",
                },
            ])
        elif actor_role == "Deployer":
            obligations.extend([
                {
                    "key": "deployer_high_risk_operations",
                    "article": "Article 26",
                    "owner_role": "Deployer",
                    "status": "required",
                    "evidence_domain": "deployer_controls",
                    "summary": "Use the system according to instructions, assign competent human oversight, monitor operation, and keep available logs for at least six months.",
                },
                {
                    "key": "dpia_linkage",
                    "article": "Article 26(9)",
                    "owner_role": "Deployer",
                    "status": "conditional",
                    "evidence_domain": "privacy_dpia",
                    "summary": "Use provider information to support GDPR or law-enforcement DPIA duties where applicable.",
                },
            ])
            if _fria_likely_required(answers):
                obligations.append({
                    "key": "fundamental_rights_impact_assessment",
                    "article": "Article 27",
                    "owner_role": "Deployer",
                    "status": "required",
                    "evidence_domain": "governance_fria",
                    "summary": "Perform and keep a FRIA before deployment, then update it when material changes occur.",
                })
            else:
                obligations.append({
                    "key": "fundamental_rights_impact_assessment_screening",
                    "article": "Article 27",
                    "owner_role": "Deployer",
                    "status": "screening_required",
                    "evidence_domain": "governance_fria",
                    "summary": "Record why FRIA is or is not required for this deployer and use case.",
                })
        else:
            obligations.append({
                "key": "importer_distributor_verification",
                "article": "Articles 23-24",
                "owner_role": actor_role,
                "status": "review_required",
                "evidence_domain": "value_chain_review",
                "summary": "Verify high-risk system documentation and compliance duties for importer/distributor role.",
            })

    if answers.get("has_transparency_obligation", False):
        obligations.append({
            "key": "transparency_notice",
            "article": "Article 50",
            "owner_role": actor_role,
            "status": "required",
            "evidence_domain": "transparency",
            "summary": "Provide notices or disclosures for chatbot, synthetic content, emotion recognition, biometric categorisation, or deepfake use cases.",
        })

    return obligations


def legal_basis_for_classification(classification: str, answers: dict[str, Any]) -> list[dict[str, str]]:
    keys = ["art_4"]
    if classification == "Prohibited AI System":
        keys.append("art_5")
    if classification == "High-Risk AI System":
        keys.extend(["art_6_annex_iii", "art_26", "art_27", "art_72", "art_73"])
    if answers.get("has_transparency_obligation", False):
        keys.append("art_50")
    return article_refs(*keys)


def serious_incident_deadline(created_at: datetime | None, incident_type: str) -> datetime:
    base = created_at or datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    if incident_type == "widespread_infringement":
        return base + timedelta(days=2)
    if incident_type == "death":
        return base + timedelta(days=10)
    return base + timedelta(days=15)


def _fria_likely_required(answers: dict[str, Any]) -> bool:
    return bool(
        answers.get("is_public_body")
        or answers.get("provides_public_service")
        or answers.get("annex_iii_area") in {"essential_services_credit", "insurance_risk_assessment"}
        or answers.get("fria_required")
    )
