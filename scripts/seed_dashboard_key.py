"""
Seed script: creates a default tenant, API key, entitlements, and demo records
for dashboard development.
Run once:  python scripts/seed_dashboard_key.py
"""
import sys, os, time, uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.exc import OperationalError

from app.db import SessionLocal
from app.models import AiFeature, AiSystem, Entitlement, Tenant, ApiKey, TenantAuthPolicy, TenantUser
from app.services.hashing import hash_api_key
from app.services.compliance_control_service import ComplianceControlService

APP_ENV = os.getenv("APP_ENV", "development")
TENANT_ID = os.getenv("DASHBOARD_TENANT_ID", "tenant-dashboard-dev")
TENANT_NAME = os.getenv("DASHBOARD_TENANT_NAME", "Dashboard Dev Tenant")
RAW_API_KEY = os.getenv("DASHBOARD_API_KEY")
KEY_ID = os.getenv("DASHBOARD_KEY_ID", f"key-dashboard-{APP_ENV}")
DEMO_SYSTEM_ID = "sys-dashboard-demo"
DEMO_FEATURE_ID = "dashboard_demo_assistant"
DB_RETRIES = int(os.getenv("SEED_DB_RETRIES", "5"))
DB_RETRY_DELAY_SECONDS = float(os.getenv("SEED_DB_RETRY_DELAY_SECONDS", "2"))
DASHBOARD_OWNER_EMAIL = (os.getenv("DASHBOARD_OWNER_EMAIL") or "dashboard-admin@local").strip().lower()
DASHBOARD_OWNER_NAME = os.getenv("DASHBOARD_OWNER_NAME", "Dashboard Owner")

ENTITLEMENTS = [
    "report_generation",
    "fria_management",
    "oversight_management",
    "incident_management",
]


def _csv_values(env_name: str) -> list[str]:
    return [value.strip().lower().removeprefix("@") for value in os.getenv(env_name, "").split(",") if value.strip()]

def seed():
    for attempt in range(1, DB_RETRIES + 1):
        try:
            return _seed_once()
        except OperationalError as exc:
            if attempt == DB_RETRIES:
                raise
            delay = DB_RETRY_DELAY_SECONDS * attempt
            print(f"Database connection failed during seed attempt {attempt}/{DB_RETRIES}; retrying in {delay:.1f}s.")
            print(str(exc).splitlines()[0])
            time.sleep(delay)


def _seed_once():
    raw_api_key = RAW_API_KEY
    if not raw_api_key and APP_ENV == "development":
        raw_api_key = "test_api_key"
    if not raw_api_key:
        raise RuntimeError("DASHBOARD_API_KEY must be set outside development.")

    db = SessionLocal()
    try:
        # Upsert tenant
        tenant = db.query(Tenant).filter(Tenant.tenant_id == TENANT_ID).first()
        if not tenant:
            tenant = Tenant(tenant_id=TENANT_ID, name=TENANT_NAME)
            db.add(tenant)
            db.flush()
            print(f"Created tenant: {TENANT_ID}")
        else:
            print(f"Tenant already exists: {TENANT_ID}")

        policy = db.query(TenantAuthPolicy).filter(TenantAuthPolicy.tenant_id == TENANT_ID).first()
        if not policy:
            policy = TenantAuthPolicy(
                tenant_id=TENANT_ID,
                allowed_domains_json=_csv_values("GOOGLE_OIDC_ALLOWED_DOMAINS"),
                allowed_emails_json=_csv_values("GOOGLE_OIDC_ALLOWED_EMAILS"),
                auto_provision_google_users=True,
                default_role="viewer",
            )
            db.add(policy)
            print("Created tenant authentication policy")
        else:
            seed_domains = _csv_values("GOOGLE_OIDC_ALLOWED_DOMAINS")
            seed_emails = _csv_values("GOOGLE_OIDC_ALLOWED_EMAILS")
            if seed_domains and not policy.allowed_domains_json:
                policy.allowed_domains_json = seed_domains
                print("Applied Google allowed domains from deployment configuration")
            if seed_emails and not policy.allowed_emails_json:
                policy.allowed_emails_json = seed_emails
                print("Applied Google allowed emails from deployment configuration")

        if DASHBOARD_OWNER_EMAIL:
            owner = db.query(TenantUser).filter(
                TenantUser.tenant_id == TENANT_ID,
                TenantUser.email == DASHBOARD_OWNER_EMAIL,
            ).first()
            if not owner:
                db.add(TenantUser(
                    id=f"usr_{uuid.uuid4().hex}",
                    tenant_id=TENANT_ID,
                    email=DASHBOARD_OWNER_EMAIL,
                    name=DASHBOARD_OWNER_NAME,
                    role="owner",
                    status="active",
                    auth_provider="password",
                ))
                print(f"Created tenant owner user: {DASHBOARD_OWNER_EMAIL}")

        # Upsert API key — always re-hash so the stored digest stays in sync
        # with the current hashing algorithm (e.g. after a SHA-256 → HMAC migration).
        key_hash = hash_api_key(raw_api_key)
        existing = db.query(ApiKey).filter(ApiKey.key_id == KEY_ID).first()
        if not existing:
            api_key = ApiKey(
                key_id=KEY_ID,
                tenant_id=TENANT_ID,
                name="Dashboard Dev Key",
                key_hash=key_hash,
                role="admin",
                scopes=["admin"],
                revoked=False,
            )
            db.add(api_key)
            if APP_ENV == "development":
                print(f"Created API key: {raw_api_key}  (hash: {key_hash[:16]}...)")
            else:
                print(f"Created API key: {KEY_ID}  (hash: {key_hash[:16]}...)")
        else:
            existing.key_hash = key_hash  # re-hash with current algorithm on every seed
            print(f"Updated API key hash: {KEY_ID}  (hash: {key_hash[:16]}...)")

        for feature_key in ENTITLEMENTS:
            entitlement = db.query(Entitlement).filter(
                Entitlement.tenant_id == TENANT_ID,
                Entitlement.feature_key == feature_key,
            ).first()
            if not entitlement:
                db.add(Entitlement(
                    id=str(uuid.uuid4()),
                    tenant_id=TENANT_ID,
                    feature_key=feature_key,
                    is_enabled=True,
                ))
                print(f"Granted entitlement: {feature_key}")

        system = db.query(AiSystem).filter(
            AiSystem.tenant_id == TENANT_ID,
            AiSystem.id == DEMO_SYSTEM_ID,
        ).first()
        if not system:
            system = AiSystem(
                id=DEMO_SYSTEM_ID,
                tenant_id=TENANT_ID,
                name="Dashboard Demo Assistant",
                description="Demo AI system for local product review.",
                deployment_status="draft",
                registration_status="draft",
            )
            db.add(system)
            db.flush()
            print(f"Created AI system: {DEMO_SYSTEM_ID}")

        feature = db.query(AiFeature).filter(
            AiFeature.tenant_id == TENANT_ID,
            AiFeature.feature_id == DEMO_FEATURE_ID,
        ).first()
        if not feature:
            db.add(AiFeature(
                id=str(uuid.uuid4()),
                tenant_id=TENANT_ID,
                ai_system_id=DEMO_SYSTEM_ID,
                feature_id=DEMO_FEATURE_ID,
                name="Demo Support Assistant",
                slug=DEMO_FEATURE_ID,
                description="Demo governed feature linked to the local dashboard system.",
                owner_email="owner@example.com",
                team="product",
                use_case="customer_support",
                decision_impact="assistive",
                affected_user_groups=["customers"],
                risk_level_current="low",
                compliance_status="active",
                fria_likely_required=False,
                approved_providers=["openai"],
                approved_models=["gpt-4.1-nano"],
            ))
            print(f"Created AI feature: {DEMO_FEATURE_ID}")

        db.commit()
        ComplianceControlService.seed_baseline(db, TENANT_ID)
        ComplianceControlService.seed_baseline(db, TENANT_ID, DEMO_SYSTEM_ID)
        if APP_ENV == "development":
            print("Done. Dashboard can now authenticate with x-api-key: test_api_key")
        else:
            print("Done. Dashboard API key is stored in Secret Manager.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
