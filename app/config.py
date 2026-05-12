import os
from dotenv import load_dotenv

load_dotenv()

def get_secret(secret_name: str, default: str | None = None) -> str | None:
    """Read secret from mounted volume (Cloud Run) or fallback to env var."""
    secret_path = f"/secrets/{secret_name}"
    if os.path.isfile(secret_path):
        with open(secret_path, "r") as f:
            return f.read().strip()
    return os.getenv(secret_name, default)


OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
DEFAULT_MODEL = get_secret("DEFAULT_MODEL", "gpt-4.1-nano")
DATABASE_URL = get_secret("DATABASE_URL", "sqlite:///./app/data/app.db")
APP_ENV = get_secret("APP_ENV", "development")
FEATURE_ID_ENFORCEMENT = get_secret("FEATURE_ID_ENFORCEMENT", "warn").lower()
CANDIDATE_VERSION_POLICY = get_secret("CANDIDATE_VERSION_POLICY", "allow_with_warning").lower()
EVIDENCE_CHAIN_MODE = get_secret("EVIDENCE_CHAIN_MODE", "best_effort_tenant_chain")
EVIDENCE_HMAC_SECRET = get_secret("EVIDENCE_HMAC_SECRET")

FIRECRAWL_API_KEY = get_secret("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = get_secret("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v1")
FIRECRAWL_ALLOWED_DOMAINS = get_secret("FIRECRAWL_ALLOWED_DOMAINS", "")

STRIPE_API_KEY = get_secret("STRIPE_API_KEY", "sk_test_mock")
STRIPE_WEBHOOK_SECRET = get_secret("STRIPE_WEBHOOK_SECRET", "whsec_mock")
FRONTEND_URL = get_secret("FRONTEND_URL", "http://localhost:3000")


try:
    FIRECRAWL_TIMEOUT = int(get_secret("FIRECRAWL_TIMEOUT", "30"))
    if FIRECRAWL_TIMEOUT <= 0:
        raise ValueError
except ValueError:
    raise RuntimeError("FIRECRAWL_TIMEOUT must be a positive integer.")

try:
    FIRECRAWL_MAX_PAGES = int(get_secret("FIRECRAWL_MAX_PAGES", "50"))
    if FIRECRAWL_MAX_PAGES <= 0:
        raise ValueError
except ValueError:
    raise RuntimeError("FIRECRAWL_MAX_PAGES must be a positive integer.")

VALID_FEATURE_ENFORCEMENT_MODES = {"warn", "quarantine", "block"}
VALID_CANDIDATE_VERSION_POLICIES = {"allow_with_warning", "quarantine", "block"}

if FEATURE_ID_ENFORCEMENT not in VALID_FEATURE_ENFORCEMENT_MODES:
    raise RuntimeError(f"Invalid FEATURE_ID_ENFORCEMENT={FEATURE_ID_ENFORCEMENT}")

if CANDIDATE_VERSION_POLICY not in VALID_CANDIDATE_VERSION_POLICIES:
    raise RuntimeError(f"Invalid CANDIDATE_VERSION_POLICY={CANDIDATE_VERSION_POLICY}")

if not EVIDENCE_HMAC_SECRET:
    raise RuntimeError("EVIDENCE_HMAC_SECRET is missing. Add it to .env.")
