import pytest
from fastapi.testclient import TestClient
from app.models import ApiKey, Tenant, TenantSubscription, Entitlement, UsageMeter
from app.services.hashing import hash_api_key
from unittest.mock import patch
import json

BILLING_ADMIN_KEY = "aigw_billing_admin_key_456"

@pytest.fixture
def tenant_fixture(db_session):
    tenant = Tenant(tenant_id="tenant-123", name="Test Tenant")
    db_session.add(tenant)
    db_session.add(ApiKey(
        key_id="billing-admin-key",
        tenant_id="tenant-123",
        name="Billing Admin Key",
        key_hash=hash_api_key(BILLING_ADMIN_KEY),
        role="admin",
        scopes=["admin", "billing:manage"],
        revoked=False,
    ))
    db_session.commit()
    db_session.refresh(tenant)
    return tenant

def test_get_subscription(client: TestClient, tenant_fixture, db_session):
    headers = {"Authorization": "Bearer test_api_key"}
    
    # We need to mock the auth to return the tenant.
    # Actually, in this codebase auth_context depends on API key in DB.
    from app.models import ApiKey
    api_key = ApiKey(key_id="test_key_id", tenant_id="tenant-123", name="Test Key", key_hash="mocked_hash")
    db_session.add(api_key)
    db_session.commit()
    
    # Mocking verify_api_key or just using the mocked token
    with patch("app.routes.billing.authenticate_api_key", return_value={"tenant_id": "tenant-123", "role": "admin"}):
        response = client.get("/v1/billing/subscription", headers=headers)
        
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant-123"
    assert data["plan_id"] == "free"
    assert data["status"] == "active"

def test_create_checkout_session(client: TestClient, tenant_fixture, db_session):
    headers = {"x-api-key": BILLING_ADMIN_KEY}

    with patch("app.routes.billing.authenticate_api_key", return_value={"tenant_id": "tenant-123", "role": "admin"}):
        response = client.post(
            "/v1/billing/checkout-session",
            headers=headers,
            json={"plan_id": "price_mock"}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "mock-checkout" in data["checkout_url"]

def test_stripe_webhook_checkout_completed(client: TestClient, db_session, tenant_fixture):
    # Stripe webhook for checkout completed
    event_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "tenant-123",
                "customer": "cus_mock_456",
                "subscription": "sub_mock_789"
            }
        }
    }
    
    with patch("app.routes.webhooks_stripe.verify_webhook_signature", return_value=event_payload):
        response = client.post("/v1/webhooks/stripe", json=event_payload, headers={"stripe-signature": "mock_sig"})
        
    assert response.status_code == 200
    
    sub = db_session.query(TenantSubscription).filter_by(tenant_id="tenant-123").first()
    assert sub.stripe_customer_id == "cus_mock_456"
    assert sub.stripe_subscription_id == "sub_mock_789"

def test_record_usage(client: TestClient, db_session, tenant_fixture):
    from app.services.billing_service import record_usage
    record_usage(db_session, "tenant-123", "governed_call", 1)
    record_usage(db_session, "tenant-123", "governed_call", 2)
    
    meter = db_session.query(UsageMeter).filter_by(tenant_id="tenant-123").first()
    assert meter is not None
    assert meter.count == 3

def test_create_portal_session(client: TestClient, tenant_fixture, db_session):
    headers = {"x-api-key": BILLING_ADMIN_KEY}

    with patch("app.routes.billing.authenticate_api_key", return_value={"tenant_id": "tenant-123", "role": "admin"}):
        response = client.post(
            "/v1/billing/portal-session",
            headers=headers
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "mock-portal" in data["portal_url"]
    assert "cus_mock_tenant-123" in data["portal_url"]

def test_get_entitlements(client: TestClient, tenant_fixture, db_session):
    from app.services.entitlement_service import grant_entitlement
    grant_entitlement(db_session, "tenant-123", "premium_feature", 100)
    
    headers = {"Authorization": "Bearer test_api_key"}
    
    with patch("app.routes.billing.authenticate_api_key", return_value={"tenant_id": "tenant-123", "role": "admin"}):
        response = client.get("/v1/billing/entitlements", headers=headers)
        
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["feature_key"] == "premium_feature"
    assert data[0]["is_enabled"] is True
    assert data[0]["limit_value"] == 100

def test_stripe_webhook_subscription_updated(client: TestClient, db_session, tenant_fixture):
    # Setup initial sub
    sub = TenantSubscription(tenant_id="tenant-123", stripe_subscription_id="sub_mock_123")
    db_session.add(sub)
    db_session.commit()

    event_payload = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_mock_123",
                "customer": "cus_mock_123",
                "status": "past_due",
                "items": {"data": [{"price": {"id": "price_pro"}}]},
                "current_period_end": 1700000000
            }
        }
    }
    
    with patch("app.routes.webhooks_stripe.verify_webhook_signature", return_value=event_payload):
        response = client.post("/v1/webhooks/stripe", json=event_payload, headers={"stripe-signature": "mock_sig"})
        
    assert response.status_code == 200
    
    db_session.refresh(sub)
    assert sub.status == "past_due"
    assert sub.plan_id == "price_pro"
    assert sub.current_period_end.timestamp() == 1700000000

def test_stripe_webhook_invalid_signature(client: TestClient):
    with patch("app.routes.webhooks_stripe.verify_webhook_signature", side_effect=ValueError("Invalid signature")):
        response = client.post("/v1/webhooks/stripe", json={}, headers={"stripe-signature": "bad_sig"})
        
    assert response.status_code == 400
    assert "Invalid signature" in response.json()["error"]["message"]

def test_tenant_isolation(client: TestClient, db_session, tenant_fixture):
    # Setup another tenant
    tenant2 = Tenant(tenant_id="tenant-456", name="Other Tenant")
    db_session.add(tenant2)
    db_session.commit()
    
    from app.services.entitlement_service import grant_entitlement
    from app.services.billing_service import record_usage
    grant_entitlement(db_session, "tenant-456", "premium_feature", 50)
    record_usage(db_session, "tenant-456", "governed_call", 10)
    
    # Authenticate as tenant-123
    headers = {"Authorization": "Bearer test_api_key"}
    with patch("app.routes.billing.authenticate_api_key", return_value={"tenant_id": "tenant-123", "role": "admin"}):
        response = client.get("/v1/billing/entitlements", headers=headers)
        
    assert response.status_code == 200
    assert len(response.json()) == 0  # tenant-123 should not see tenant-456's entitlements
