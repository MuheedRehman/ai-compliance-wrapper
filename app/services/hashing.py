import hashlib
import hmac
import json
from typing import Any
from app.config import API_KEY_PEPPER, EVIDENCE_HMAC_SECRET


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_object(data: Any) -> str:
    return sha256_text(stable_json(data))


def hmac_signature(data: Any) -> str:
    message = stable_json(data).encode("utf-8")
    secret = EVIDENCE_HMAC_SECRET.encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def hash_api_key(api_key: str) -> str:
    """HMAC-SHA256 keyed with a server-side pepper to prevent rainbow table attacks.
    Falls back to EVIDENCE_HMAC_SECRET if API_KEY_PEPPER is not explicitly configured."""
    pepper = (API_KEY_PEPPER or EVIDENCE_HMAC_SECRET or "").encode("utf-8")
    return hmac.new(pepper, api_key.encode("utf-8"), hashlib.sha256).hexdigest()
