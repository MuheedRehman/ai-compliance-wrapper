from __future__ import annotations

from copy import deepcopy
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
    "art_8_15": {
        "article": "Articles 8-15",
        "title": "Requirements for high-risk AI systems",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-8",
    },
    "art_16": {
        "article": "Article 16",
        "title": "Provider obligations for high-risk AI systems",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-16",
    },
    "art_23_24": {
        "article": "Articles 23-24",
        "title": "Importer and distributor obligations",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-23",
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
    "art_53": {
        "article": "Article 53",
        "title": "Obligations for providers of general-purpose AI models",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-53",
    },
    "art_55": {
        "article": "Article 55",
        "title": "Obligations for providers of GPAI models with systemic risk",
        "source_url": f"{AI_ACT_SERVICE_DESK_BASE}/article-55",
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


def _dimension(
    *,
    dimension_id: str,
    pillar: str,
    chapter: str,
    article_keys: list[str],
    annex_refs: list[str] | None = None,
    actor_roles: list[str],
    risk_tiers: list[str],
    trigger_conditions: list[str],
    required_controls: list[dict[str, str]],
    required_evidence: list[dict[str, str]],
    scanner_signals: list[str],
    effective_dates: dict[str, str],
    confidence_policy: str,
    obligation_status: str,
    evidence_domain: str,
    summary: str,
    explanation_template: str,
    applies_when: dict[str, Any],
) -> dict[str, Any]:
    articles = article_refs(*article_keys)
    return {
        "dimension_id": dimension_id,
        "pillar": pillar,
        "chapter": chapter,
        "articles": articles,
        "article": articles[0]["article"] if articles else "EU AI Act",
        "annex_refs": annex_refs or [],
        "actor_roles": actor_roles,
        "risk_tiers": risk_tiers,
        "trigger_conditions": trigger_conditions,
        "required_controls": required_controls,
        "required_evidence": required_evidence,
        "scanner_signals": scanner_signals,
        "effective_dates": effective_dates,
        "confidence_policy": confidence_policy,
        "obligation_status": obligation_status,
        "evidence_domain": evidence_domain,
        "summary": summary,
        "explanation_template": explanation_template,
        "applies_when": applies_when,
    }


COMPLIANCE_DIMENSIONS: list[dict[str, Any]] = [
    _dimension(
        dimension_id="ai_literacy",
        pillar="AI Literacy",
        chapter="Chapter I: General Provisions",
        article_keys=["art_4"],
        actor_roles=["Provider", "Deployer", "Importer/Distributor"],
        risk_tiers=["all"],
        trigger_conditions=["Always required for providers and deployers using or operating AI systems."],
        required_controls=[{"control_key": "ai_literacy_program", "title": "AI literacy program and training evidence"}],
        required_evidence=[{"type": "policy", "domain": "ai_literacy"}, {"type": "training_record", "domain": "ai_literacy"}],
        scanner_signals=["public AI policy", "responsible AI training", "governance documentation"],
        effective_dates={"applies_from": "2025-02-02"},
        confidence_policy="Always applies; evidence confidence depends on training records and role-specific policy coverage.",
        obligation_status="required",
        evidence_domain="ai_literacy",
        summary="Maintain role-appropriate AI literacy for staff and operators.",
        explanation_template="Because the organisation operates or provides AI systems, Article 4 AI literacy evidence is required.",
        applies_when={"always": True},
    ),
    _dimension(
        dimension_id="prohibited_practice_review",
        pillar="Prohibited Practices",
        chapter="Chapter II: Prohibited AI Practices",
        article_keys=["art_5"],
        actor_roles=["Provider", "Deployer", "Importer/Distributor"],
        risk_tiers=["prohibited"],
        trigger_conditions=["Intake or scanner indicates a prohibited AI practice."],
        required_controls=[{"control_key": "prohibited_use_review", "title": "Cease, redesign, or legal escalation for prohibited use"}],
        required_evidence=[{"type": "risk_assessment", "domain": "classification"}, {"type": "legal_review", "domain": "classification"}],
        scanner_signals=["emotion recognition", "biometric categorisation", "social scoring", "manipulative use", "law enforcement biometric use"],
        effective_dates={"applies_from": "2025-02-02"},
        confidence_policy="Blocking path; low-confidence scanner matches require manual legal review before product use.",
        obligation_status="blocking",
        evidence_domain="classification",
        summary="Cease or redesign the prohibited use before deployment.",
        explanation_template="Because the intake marks prohibited-use risk, Article 5 review is blocking before deployment.",
        applies_when={"answer_true": "is_prohibited_use"},
    ),
    _dimension(
        dimension_id="high_risk_classification",
        pillar="High-Risk Classification",
        chapter="Chapter III Section 1: Classification of AI Systems as High-Risk",
        article_keys=["art_6_annex_iii"],
        annex_refs=["Annex III"],
        actor_roles=["Provider", "Deployer", "Importer/Distributor"],
        risk_tiers=["high-risk"],
        trigger_conditions=["System is marked as Annex III high-risk or as a safety component of regulated products."],
        required_controls=[{"control_key": "high_risk_classification_record", "title": "High-risk classification rationale and Annex mapping"}],
        required_evidence=[{"type": "risk_assessment", "domain": "classification"}, {"type": "intake_record", "domain": "classification"}],
        scanner_signals=["hiring", "education", "credit", "insurance", "law enforcement", "migration", "critical infrastructure"],
        effective_dates={"annex_iii_applies_from": "2026-08-02", "safety_component_applies_from": "2027-08-02"},
        confidence_policy="Manual review required unless Annex III category and intended purpose are explicit.",
        obligation_status="required",
        evidence_domain="classification",
        summary="Record high-risk basis, intended purpose, Annex category, and classification confidence.",
        explanation_template="Because the system is high-risk by Annex III or safety-component flags, Article 6 classification evidence is required.",
        applies_when={"classification": "High-Risk AI System"},
    ),
    _dimension(
        dimension_id="provider_high_risk_requirements",
        pillar="High-Risk Provider Requirements",
        chapter="Chapter III Sections 2-3: High-Risk Requirements and Provider Obligations",
        article_keys=["art_8_15", "art_16"],
        actor_roles=["Provider"],
        risk_tiers=["high-risk"],
        trigger_conditions=["Actor is provider and system is high-risk."],
        required_controls=[
            {"control_key": "risk_management_system", "title": "Risk management system"},
            {"control_key": "data_governance", "title": "Data and data governance evidence"},
            {"control_key": "technical_documentation", "title": "Technical documentation"},
            {"control_key": "human_oversight_design", "title": "Human oversight design"},
            {"control_key": "robustness_cybersecurity", "title": "Accuracy, robustness, and cybersecurity evidence"},
        ],
        required_evidence=[
            {"type": "risk_assessment", "domain": "risk_management"},
            {"type": "technical_documentation", "domain": "technical_documentation"},
            {"type": "model_card", "domain": "model_documentation"},
            {"type": "test_result", "domain": "robustness_cybersecurity"},
        ],
        scanner_signals=["model card", "technical documentation", "security page", "audit logs", "human oversight"],
        effective_dates={"annex_iii_applies_from": "2026-08-02", "safety_component_applies_from": "2027-08-02"},
        confidence_policy="High confidence only when risk, data, documentation, oversight, logging, and testing evidence are linked.",
        obligation_status="required",
        evidence_domain="provider_controls",
        summary="Implement provider obligations including risk management, data governance, technical documentation, logging, oversight, robustness, and conformity readiness.",
        explanation_template="Because the actor is the provider of a high-risk AI system, Articles 8-16 provider obligations apply.",
        applies_when={"classification": "High-Risk AI System", "actor_role": "Provider"},
    ),
    _dimension(
        dimension_id="deployer_high_risk_operations",
        pillar="High-Risk Deployer Operations",
        chapter="Chapter III Section 3: Obligations of Deployers",
        article_keys=["art_26"],
        actor_roles=["Deployer"],
        risk_tiers=["high-risk"],
        trigger_conditions=["Actor is deployer and system is high-risk."],
        required_controls=[
            {"control_key": "instructions_for_use", "title": "Use according to provider instructions"},
            {"control_key": "human_oversight_assignment", "title": "Competent human oversight"},
            {"control_key": "operation_monitoring", "title": "Operational monitoring"},
            {"control_key": "log_retention", "title": "High-risk log retention"},
        ],
        required_evidence=[
            {"type": "human_oversight", "domain": "deployer_controls"},
            {"type": "log_extract", "domain": "log_retention"},
            {"type": "policy", "domain": "deployer_controls"},
        ],
        scanner_signals=["human oversight", "appeals", "audit logs", "monitoring", "incident process"],
        effective_dates={"annex_iii_applies_from": "2026-08-02"},
        confidence_policy="Requires operating evidence, not only public policy language.",
        obligation_status="required",
        evidence_domain="deployer_controls",
        summary="Use the system according to instructions, assign competent human oversight, monitor operation, and keep available logs.",
        explanation_template="Because the actor is a deployer of a high-risk AI system, Article 26 operational duties apply.",
        applies_when={"classification": "High-Risk AI System", "actor_role": "Deployer"},
    ),
    _dimension(
        dimension_id="fria_screening",
        pillar="Fundamental Rights Impact Assessment",
        chapter="Chapter III Section 3: FRIA",
        article_keys=["art_27"],
        actor_roles=["Deployer"],
        risk_tiers=["high-risk"],
        trigger_conditions=["High-risk deployer scenario; FRIA required for public bodies, public services, or qualifying Annex III cases."],
        required_controls=[{"control_key": "fria_screening", "title": "FRIA applicability screening and assessment record"}],
        required_evidence=[{"type": "fria", "domain": "governance_fria"}, {"type": "approval_record", "domain": "governance_fria"}],
        scanner_signals=["public service", "fundamental rights", "affected persons", "appeals", "human review"],
        effective_dates={"applies_from": "2026-08-02"},
        confidence_policy="If FRIA trigger facts are incomplete, require screening and legal review.",
        obligation_status="screening_required",
        evidence_domain="governance_fria",
        summary="Record why FRIA is or is not required, and perform it before deployment when triggered.",
        explanation_template="Because this is a high-risk deployer scenario, Article 27 FRIA screening is required.",
        applies_when={"classification": "High-Risk AI System", "actor_role": "Deployer"},
    ),
    _dimension(
        dimension_id="importer_distributor_verification",
        pillar="Importer and Distributor Verification",
        chapter="Chapter III Section 3: Other Economic Operators",
        article_keys=["art_23_24"],
        actor_roles=["Importer/Distributor"],
        risk_tiers=["high-risk"],
        trigger_conditions=["Actor is neither provider nor deployer for a high-risk system."],
        required_controls=[{"control_key": "importer_distributor_verification", "title": "Value-chain compliance verification"}],
        required_evidence=[{"type": "vendor_doc", "domain": "value_chain_review"}, {"type": "declaration", "domain": "value_chain_review"}],
        scanner_signals=["vendor documentation", "CE marking", "declaration of conformity", "instructions for use"],
        effective_dates={"applies_from": "2026-08-02"},
        confidence_policy="Requires manual review because importer/distributor duties depend on value-chain role.",
        obligation_status="review_required",
        evidence_domain="value_chain_review",
        summary="Verify high-risk system documentation and compliance duties for importer/distributor role.",
        explanation_template="Because the actor is an importer or distributor for a high-risk AI system, Articles 23-24 verification duties need review.",
        applies_when={"classification": "High-Risk AI System", "actor_role": "Importer/Distributor"},
    ),
    _dimension(
        dimension_id="transparency_notice",
        pillar="Transparency for Certain AI Systems",
        chapter="Chapter IV: Transparency Obligations",
        article_keys=["art_50"],
        actor_roles=["Provider", "Deployer", "Importer/Distributor"],
        risk_tiers=["limited-risk", "transparency"],
        trigger_conditions=["System uses chatbot, synthetic content, deepfake, emotion recognition, or biometric categorisation transparency features."],
        required_controls=[{"control_key": "transparency_notice", "title": "User-facing AI disclosure and synthetic-content notice"}],
        required_evidence=[{"type": "screenshot", "domain": "transparency"}, {"type": "policy", "domain": "transparency"}],
        scanner_signals=["AI disclosure", "chatbot label", "deepfake label", "synthetic media label", "watermark"],
        effective_dates={"applies_from": "2026-08-02"},
        confidence_policy="Scanner confidence rises when disclosure appears near AI interaction surfaces, not only in generic policy text.",
        obligation_status="required",
        evidence_domain="transparency",
        summary="Provide notices or disclosures for chatbot, synthetic content, emotion recognition, biometric categorisation, or deepfake use cases.",
        explanation_template="Because transparency-triggering functionality is present, Article 50 disclosure evidence is required.",
        applies_when={"answer_true": "has_transparency_obligation"},
    ),
    _dimension(
        dimension_id="gpai_provider_obligations",
        pillar="GPAI Provider Obligations",
        chapter="Chapter V: General-Purpose AI Models",
        article_keys=["art_53"],
        actor_roles=["Provider"],
        risk_tiers=["gpai"],
        trigger_conditions=["System is identified as a general-purpose AI model or GPAI provider scenario."],
        required_controls=[
            {"control_key": "gpai_technical_documentation", "title": "GPAI technical documentation"},
            {"control_key": "gpai_copyright_policy", "title": "Copyright/TDM policy and training-data summary"},
        ],
        required_evidence=[
            {"type": "technical_documentation", "domain": "gpai_documentation"},
            {"type": "policy", "domain": "gpai_copyright"},
            {"type": "training_data_summary", "domain": "gpai_copyright"},
        ],
        scanner_signals=["foundation model", "general purpose model", "training data", "copyright policy", "model documentation"],
        effective_dates={"new_models_apply_from": "2025-08-02", "pre_existing_models_apply_from": "2027-08-02"},
        confidence_policy="Manual review required when the product only consumes third-party GPAI rather than providing a model.",
        obligation_status="required",
        evidence_domain="gpai_documentation",
        summary="Maintain GPAI technical documentation, downstream information, copyright policy, and training-data summary evidence.",
        explanation_template="Because the system is marked as GPAI, Article 53 provider obligations must be assessed.",
        applies_when={"answer_true": "is_gpai"},
    ),
    _dimension(
        dimension_id="gpai_systemic_risk",
        pillar="GPAI Systemic Risk",
        chapter="Chapter V: GPAI Models with Systemic Risk",
        article_keys=["art_55"],
        actor_roles=["Provider"],
        risk_tiers=["gpai-systemic-risk"],
        trigger_conditions=["GPAI model is flagged as systemic risk or equivalent risk review is required."],
        required_controls=[{"control_key": "gpai_systemic_risk_evaluation", "title": "GPAI systemic-risk evaluation and mitigation"}],
        required_evidence=[{"type": "test_result", "domain": "gpai_systemic_risk"}, {"type": "risk_assessment", "domain": "gpai_systemic_risk"}],
        scanner_signals=["systemic risk", "frontier model", "model evaluation", "red teaming", "safety report"],
        effective_dates={"applies_from": "2025-08-02"},
        confidence_policy="Requires human review unless systemic-risk designation is explicit.",
        obligation_status="review_required",
        evidence_domain="gpai_systemic_risk",
        summary="Assess whether GPAI systemic-risk obligations apply and capture evaluation/mitigation evidence.",
        explanation_template="Because the GPAI systemic-risk flag is set, Article 55 evaluation and mitigation duties need review.",
        applies_when={"answer_true": "is_gpai_systemic_risk"},
    ),
    _dimension(
        dimension_id="post_market_monitoring",
        pillar="Post-Market Monitoring",
        chapter="Chapter IX: Post-Market Monitoring",
        article_keys=["art_72", "art_73"],
        actor_roles=["Provider"],
        risk_tiers=["high-risk"],
        trigger_conditions=["Actor is provider and system is high-risk."],
        required_controls=[
            {"control_key": "post_market_monitoring_plan", "title": "Post-market monitoring plan"},
            {"control_key": "serious_incident_reporting", "title": "Serious incident reporting workflow"},
        ],
        required_evidence=[{"type": "policy", "domain": "post_market_monitoring"}, {"type": "incident_record", "domain": "governance_incident"}],
        scanner_signals=["post-market monitoring", "incident reporting", "status page", "safety monitoring"],
        effective_dates={"applies_from": "2026-08-02"},
        confidence_policy="Requires operational monitoring evidence and incident escalation process.",
        obligation_status="required",
        evidence_domain="post_market_monitoring",
        summary="Establish post-market monitoring and serious incident reporting processes for the high-risk AI system.",
        explanation_template="Because the actor is the provider of a high-risk AI system, Articles 72-73 monitoring and incident duties apply.",
        applies_when={"classification": "High-Risk AI System", "actor_role": "Provider"},
    ),
]


def list_compliance_dimensions() -> list[dict[str, Any]]:
    return [_public_dimension(dimension) for dimension in COMPLIANCE_DIMENSIONS]


def build_obligation_graph(actor_role: str, classification: str, answers: dict[str, Any]) -> list[dict[str, Any]]:
    dimensions = applicable_dimensions(actor_role, classification, answers)
    obligations: list[dict[str, Any]] = []

    for dimension in dimensions:
        obligation = {
            "key": dimension["dimension_id"],
            "dimension_id": dimension["dimension_id"],
            "pillar": dimension["pillar"],
            "chapter": dimension["chapter"],
            "article": dimension["article"],
            "articles": dimension["articles"],
            "annex_refs": dimension["annex_refs"],
            "actor_roles": dimension["actor_roles"],
            "risk_tiers": dimension["risk_tiers"],
            "trigger_conditions": dimension["trigger_conditions"],
            "required_controls": dimension["required_controls"],
            "required_evidence": dimension["required_evidence"],
            "scanner_signals": dimension["scanner_signals"],
            "effective_dates": dimension["effective_dates"],
            "confidence_policy": dimension["confidence_policy"],
            "owner_role": _owner_role_for_dimension(actor_role, dimension),
            "status": _status_for_dimension(dimension, answers),
            "evidence_domain": dimension["evidence_domain"],
            "summary": dimension["summary"],
            "explanation": _render_explanation(dimension, actor_role, classification, answers),
        }
        obligations.append(obligation)

    return obligations


def applicable_dimensions(actor_role: str, classification: str, answers: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        deepcopy(dimension)
        for dimension in COMPLIANCE_DIMENSIONS
        if _dimension_applies(dimension, actor_role, classification, answers)
    ]


def explain_obligations(
    actor_role: str,
    classification: str,
    obligation_path: str,
    answers: dict[str, Any],
) -> dict[str, Any]:
    graph = build_obligation_graph(actor_role, classification, answers)
    controls = []
    evidence = []
    explanations = []
    manual_review_required = False

    for item in graph:
        controls.extend([
            {
                **control,
                "dimension_id": item["dimension_id"],
                "article": item["article"],
                "evidence_domain": item["evidence_domain"],
            }
            for control in item.get("required_controls", [])
        ])
        evidence.extend([
            {
                **requirement,
                "dimension_id": item["dimension_id"],
                "article": item["article"],
            }
            for requirement in item.get("required_evidence", [])
        ])
        explanations.append(item["explanation"])
        if item["status"] in {"blocking", "review_required", "screening_required"} or item["dimension_id"] == "fria_screening":
            manual_review_required = True

    return {
        "actor_role": actor_role,
        "system_classification": classification,
        "obligation_path": obligation_path,
        "applicable_dimensions": graph,
        "legal_basis": legal_basis_for_classification(classification, answers, actor_role),
        "controls_to_create": _dedupe_dicts(controls, "control_key"),
        "evidence_requirements": _dedupe_dicts(evidence, "type", "domain", "dimension_id"),
        "explanations": explanations,
        "manual_review_required": manual_review_required,
    }


def legal_basis_for_classification(
    classification: str,
    answers: dict[str, Any],
    actor_role: str | None = None,
) -> list[dict[str, str]]:
    role = actor_role or _infer_actor_role(answers)
    dimensions = applicable_dimensions(role, classification, answers)
    refs: list[dict[str, str]] = []
    seen: set[str] = set()

    for dimension in dimensions:
        for article in dimension["articles"]:
            if article["article"] in seen:
                continue
            seen.add(article["article"])
            refs.append(article)

    return refs


def serious_incident_deadline(created_at: datetime | None, incident_type: str) -> datetime:
    base = created_at or datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)

    if incident_type == "widespread_infringement":
        return base + timedelta(days=2)
    if incident_type == "death":
        return base + timedelta(days=10)
    return base + timedelta(days=15)


def _dimension_applies(
    dimension: dict[str, Any],
    actor_role: str,
    classification: str,
    answers: dict[str, Any],
) -> bool:
    rule = dimension["applies_when"]

    if rule.get("always"):
        return True

    if "answer_true" in rule and not answers.get(rule["answer_true"], False):
        return False

    if "classification" in rule and classification != rule["classification"]:
        return False

    if "actor_role" in rule and actor_role != rule["actor_role"]:
        return False

    return True


def _owner_role_for_dimension(actor_role: str, dimension: dict[str, Any]) -> str:
    if actor_role in dimension["actor_roles"]:
        return actor_role
    return dimension["actor_roles"][0]


def _status_for_dimension(dimension: dict[str, Any], answers: dict[str, Any]) -> str:
    if dimension["dimension_id"] == "fria_screening" and _fria_likely_required(answers):
        return "required"
    return dimension["obligation_status"]


def _render_explanation(
    dimension: dict[str, Any],
    actor_role: str,
    classification: str,
    answers: dict[str, Any],
) -> str:
    explanation = dimension["explanation_template"]
    if dimension["dimension_id"] == "fria_screening" and _fria_likely_required(answers):
        explanation = "Because the deployer/use-case facts indicate a likely FRIA trigger, Article 27 FRIA completion is required before deployment."
    return f"{explanation} Actor: {actor_role}. Classification: {classification}."


def _public_dimension(dimension: dict[str, Any]) -> dict[str, Any]:
    item = deepcopy(dimension)
    item.pop("applies_when", None)
    item.pop("explanation_template", None)
    item["status"] = item.pop("obligation_status")
    return item


def _dedupe_dicts(items: list[dict[str, Any]], *keys: str) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        identity = tuple(item.get(key) for key in keys)
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(item)
    return deduped


def _infer_actor_role(answers: dict[str, Any]) -> str:
    if answers.get("is_developer", False):
        return "Provider"
    if answers.get("is_deployer", False):
        return "Deployer"
    return "Importer/Distributor"


def _fria_likely_required(answers: dict[str, Any]) -> bool:
    return bool(
        answers.get("is_public_body")
        or answers.get("provides_public_service")
        or answers.get("annex_iii_area") in {"essential_services_credit", "insurance_risk_assessment"}
        or answers.get("fria_required")
    )
