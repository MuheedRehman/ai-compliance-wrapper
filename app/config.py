import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4.1-nano")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/data/app.db")
APP_ENV = os.getenv("APP_ENV", "development")
FEATURE_ID_ENFORCEMENT = os.getenv("FEATURE_ID_ENFORCEMENT", "warn").lower()
CANDIDATE_VERSION_POLICY = os.getenv("CANDIDATE_VERSION_POLICY", "allow_with_warning").lower()
EVIDENCE_CHAIN_MODE = os.getenv("EVIDENCE_CHAIN_MODE", "best_effort_tenant_chain")
EVIDENCE_HMAC_SECRET = os.getenv("EVIDENCE_HMAC_SECRET")

VALID_FEATURE_ENFORCEMENT_MODES = {"warn", "quarantine", "block"}
VALID_CANDIDATE_VERSION_POLICIES = {"allow_with_warning", "quarantine", "block"}

if FEATURE_ID_ENFORCEMENT not in VALID_FEATURE_ENFORCEMENT_MODES:
    raise RuntimeError(f"Invalid FEATURE_ID_ENFORCEMENT={FEATURE_ID_ENFORCEMENT}")

if CANDIDATE_VERSION_POLICY not in VALID_CANDIDATE_VERSION_POLICIES:
    raise RuntimeError(f"Invalid CANDIDATE_VERSION_POLICY={CANDIDATE_VERSION_POLICY}")

if not EVIDENCE_HMAC_SECRET:
    raise RuntimeError("EVIDENCE_HMAC_SECRET is missing. Add it to .env.")
