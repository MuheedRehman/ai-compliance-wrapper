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
AI_PROVIDER_MODE = get_secret("AI_PROVIDER_MODE", "live").lower()
DEFAULT_MODEL = get_secret("DEFAULT_MODEL", "gpt-4.1-nano")
DATABASE_URL = get_secret("DATABASE_URL", "sqlite:///./app/data/app.db")
APP_ENV = (get_secret("APP_ENV", "development") or "development").strip().lower()
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
VALID_AI_PROVIDER_MODES = {"live", "demo"}
PRODUCTION_ENVS = {"production", "prod"}

if FEATURE_ID_ENFORCEMENT not in VALID_FEATURE_ENFORCEMENT_MODES:
    raise RuntimeError(f"Invalid FEATURE_ID_ENFORCEMENT={FEATURE_ID_ENFORCEMENT}")

if CANDIDATE_VERSION_POLICY not in VALID_CANDIDATE_VERSION_POLICIES:
    raise RuntimeError(f"Invalid CANDIDATE_VERSION_POLICY={CANDIDATE_VERSION_POLICY}")

if AI_PROVIDER_MODE not in VALID_AI_PROVIDER_MODES:
    raise RuntimeError(f"Invalid AI_PROVIDER_MODE={AI_PROVIDER_MODE}")

def validate_runtime_config() -> None:
    if not EVIDENCE_HMAC_SECRET:
        raise RuntimeError("EVIDENCE_HMAC_SECRET is missing. Add it to .env.")

    if APP_ENV not in PRODUCTION_ENVS:
        return

    if DATABASE_URL.startswith("sqlite"):
        raise RuntimeError("Production APP_ENV cannot use a SQLite DATABASE_URL.")
    if len(EVIDENCE_HMAC_SECRET) < 32:
        raise RuntimeError("Production EVIDENCE_HMAC_SECRET must be at least 32 characters.")
    if STRIPE_API_KEY == "sk_test_mock":
        raise RuntimeError("Production STRIPE_API_KEY cannot use the mock default.")
    if STRIPE_WEBHOOK_SECRET == "whsec_mock":
        raise RuntimeError("Production STRIPE_WEBHOOK_SECRET cannot use the mock default.")
    if FRONTEND_URL.strip() == "*":
        raise RuntimeError("Production FRONTEND_URL cannot be '*'.")
    if AI_PROVIDER_MODE == "demo":
        raise RuntimeError("Production AI_PROVIDER_MODE cannot be demo.")
    if AI_PROVIDER_MODE == "live" and not OPENAI_API_KEY:
        raise RuntimeError("Production live AI_PROVIDER_MODE requires OPENAI_API_KEY.")


validate_runtime_config()
