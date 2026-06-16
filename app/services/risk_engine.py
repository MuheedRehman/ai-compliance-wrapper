import re
from dataclasses import asdict, dataclass
from typing import Any

_MAX_RISK_INPUT = 4_000  # chars — caps regex scan to bound worst-case runtime


@dataclass
class RuleResult:
    rule_id: str
    rule_group: str
    severity: str
    action: str
    description: str


def _severity_score(severity: str) -> int:
    return {
        "low": 10,
        "medium": 25,
        "high": 40,
        "critical": 60,
    }.get(severity, 10)


def pii_rules(text: str) -> list[RuleResult]:
    rules = []
    patterns = {
        # email: domain part uses [\w-]+ (no dot) so the literal \. before TLD is unambiguous
        "pii.email.detected": ("email", r"[\w.+-]+@[\w-]+\.[\w.]+"),
        "pii.phone.detected": ("phone", r"\+?\d[\d\s\-\(\)]{7,}\d"),
        # credit card: [ -]? (simple optional) instead of [ -]*? (lazy) avoids exponential backtracking
        "pii.credit_card.possible": ("credit card-like number", r"\b\d(?:[ -]?\d){12,15}\b"),
        "pii.iban.possible": ("IBAN-like identifier", r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    }
    for rule_id, (label, pattern) in patterns.items():
        if re.search(pattern, text):
            severity = "high" if "credit_card" in rule_id else "medium"
            rules.append(RuleResult(rule_id, "pii", severity, "redact", f"Detected {label}"))
    return rules


def secret_rules(text: str) -> list[RuleResult]:
    lowered = text.lower()
    terms = ["password", "api key", "private key", "secret token", "bearer token"]
    return [
        RuleResult(f"secret.keyword.{term.replace(' ', '_')}", "secrets", "high", "block", f"Detected secret-related term: {term}")
        for term in terms if term in lowered
    ]


def regulated_domain_rules(text: str, policy_context: dict[str, Any] | None = None) -> list[RuleResult]:
    lowered = text.lower()
    context_text = " ".join(str(v).lower() for v in (policy_context or {}).values())
    haystack = f"{lowered} {context_text}"
    domains = {
        "regulated.employment": ["hiring", "employment", "resume screening", "candidate ranking"],
        "regulated.finance": ["credit scoring", "loan approval", "insurance pricing"],
        "regulated.healthcare": ["medical diagnosis", "patient treatment", "healthcare triage"],
        "regulated.education": ["student scoring", "education admission"],
    }
    rules = []
    for rule_id, terms in domains.items():
        for term in terms:
            if term in haystack:
                rules.append(RuleResult(rule_id, "regulated_domain", "medium", "review", f"Detected regulated domain context: {term}"))
                break
    return rules


def assess_risk(text: str, policy_context: dict[str, Any] | None = None) -> dict:
    text = text[:_MAX_RISK_INPUT]
    results = pii_rules(text) + secret_rules(text) + regulated_domain_rules(text, policy_context)
    score = min(sum({"low": 10, "medium": 25, "high": 40, "critical": 60}.get(r.severity, 10) for r in results), 100)
    risk_level = "high" if score >= 60 else "medium" if score >= 25 else "low"
    return {
        "risk_level": risk_level,
        "risk_score": score,
        "rule_results": [asdict(r) for r in results],
        "triggered_rule_ids": sorted({r.rule_id for r in results}),
    }
