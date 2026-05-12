"""
Seed script: creates a default tenant, API key, entitlements, and demo records
for dashboard development.
Run once:  python scripts/seed_dashboard_key.py
"""
import sys, os, uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal
from app.models import AiFeature, AiSystem, Entitlement, Tenant, ApiKey
from app.services.hashing import hash_api_key
from app.services.compliance_control_service import ComplianceControlService

APP_ENV = os.getenv("APP_ENV", "development")
TENANT_ID = os.getenv("DASHBOARD_TENANT_ID", "tenant-dashboard-dev")
TENANT_NAME = os.getenv("DASHBOARD_TENANT_NAME", "Dashboard Dev Tenant")
RAW_API_KEY = os.getenv("DASHBOARD_API_KEY")
KEY_ID = os.getenv("DASHBOARD_KEY_ID", f"key-dashboard-{APP_ENV}")
DEMO_SYSTEM_ID = "sys-dashboard-demo"
DEMO_FEATURE_ID = "dashboard_demo_assistant"

ENTITLEMENTS = [
    "report_generation",
    "fria_management",
    "oversight_management",
    "incident_management",
]

def seed():
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

        # Upsert API key
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
            print(f"API key already exists: {KEY_ID}")

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
