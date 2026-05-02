import re

REDACTION_PATTERNS = [
    ("email", r"[\w\.-]+@[\w\.-]+\.\w+"),
    ("phone", r"\+?\d[\d\s\-\(\)]{7,}\d"),
    ("credit_card", r"\b(?:\d[ -]*?){13,16}\b"),
    ("iban", r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    ("secret", r"(?i)(api[_-]?key|secret|token|password|private[_-]?key)\s*[:=]\s*['\"]?[\w\-\.]{6,}"),
]


def redact_text(text: str | None) -> str | None:
    if text is None:
        return None

    redacted = text

    for label, pattern in REDACTION_PATTERNS:
        redacted = re.sub(pattern, f"[REDACTED_{label.upper()}]", redacted)

    return redacted


def redact_metadata(value):
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [redact_metadata(item) for item in value]

    if isinstance(value, dict):
        return {key: redact_metadata(item) for key, item in value.items()}

    return value
