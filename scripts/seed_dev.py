import uuid
from app.db import SessionLocal
from app.models import ApiKey, AiFeature, Tenant, TenantAuthPolicy
from app.services.hashing import hash_api_key

TENANT_ID = "tenant_demo"
APP_KEY = "aigw_dev_app_key_123"
ADMIN_KEY = "aigw_dev_admin_key_123"


def upsert_api_key(db, key_id, name, raw_key, role, scopes):
    existing = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if existing:
        existing.scopes = scopes
        existing.role = role
        existing.key_hash = hash_api_key(raw_key)
        return existing

    record = ApiKey(key_id=key_id, tenant_id=TENANT_ID, name=name, key_hash=hash_api_key(raw_key), role=role, scopes=scopes, revoked=False)
    db.add(record)
    return record


def main():
    db = SessionLocal()

    if not db.query(Tenant).filter(Tenant.tenant_id == TENANT_ID).first():
        db.add(Tenant(tenant_id=TENANT_ID, name="Demo Tenant"))

    upsert_api_key(db, "dev_app_key", "Development App Key", APP_KEY, "app", ["invoke_ai", "logs:read", "features:read"])
    upsert_api_key(db, "dev_admin_key", "Development Admin Key", ADMIN_KEY, "admin", ["invoke_ai", "logs:read", "features:read", "features:write", "reviews:read", "reviews:write", "tenant:read", "tenant:admin", "tenant:login", "admin"])

    if not db.query(TenantAuthPolicy).filter(TenantAuthPolicy.tenant_id == TENANT_ID).first():
        db.add(TenantAuthPolicy(tenant_id=TENANT_ID))

    existing_feature = db.query(AiFeature).filter(AiFeature.tenant_id == TENANT_ID, AiFeature.feature_id == "customer_support_bot").first()

    if not existing_feature:
        db.add(AiFeature(
            id=str(uuid.uuid4()),
            tenant_id=TENANT_ID,
            feature_id="customer_support_bot",
            name="Customer Support Bot",
            slug="customer_support_bot",
            description="Replies to customer support messages.",
            owner_email="founder@example.com",
            team="support",
            use_case="customer_support",
            decision_impact="assistive",
            affected_user_groups=["customers"],
            risk_level_current="low",
            compliance_status="active",
            fria_likely_required=False,
            approved_providers=["openai"],
            approved_models=["gpt-4.1-nano"],
        ))

    db.commit()
    db.close()

    print("Seed complete.")
    print(f"App key:   {APP_KEY}")
    print(f"Admin key: {ADMIN_KEY}")


if __name__ == "__main__":
    main()
