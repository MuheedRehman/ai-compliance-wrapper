from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from app.models import TenantSubscription, UsageMeter
from app.integrations.stripe_client import create_checkout_session, create_portal_session

def get_subscription(db: Session, tenant_id: str) -> TenantSubscription:
    sub = db.query(TenantSubscription).filter(TenantSubscription.tenant_id == tenant_id).first()
    if not sub:
        sub = TenantSubscription(tenant_id=tenant_id, plan_id="free", status="active")
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

def create_checkout(db: Session, tenant_id: str, plan_id: str) -> str:
    # Ensure tenant exists or subscription is tracked
    get_subscription(db, tenant_id)
    return create_checkout_session(tenant_id, plan_id)

def create_portal(db: Session, tenant_id: str) -> str:
    sub = get_subscription(db, tenant_id)
    customer_id = sub.stripe_customer_id or f"cus_mock_{tenant_id}"
    return create_portal_session(customer_id)

def handle_stripe_webhook(db: Session, event_type: str, data: dict):
    # Depending on event type, update subscription
    # We mainly care about checkout.session.completed, customer.subscription.updated
    
    if event_type == "checkout.session.completed":
        session_obj = data.get("object", {}) if isinstance(data, dict) else getattr(data, "object", {})
        
        tenant_id = session_obj.get("client_reference_id") if isinstance(session_obj, dict) else getattr(session_obj, "client_reference_id", None)
        customer_id = session_obj.get("customer") if isinstance(session_obj, dict) else getattr(session_obj, "customer", None)
        subscription_id = session_obj.get("subscription") if isinstance(session_obj, dict) else getattr(session_obj, "subscription", None)
        
        if tenant_id:
            sub = get_subscription(db, tenant_id)
            sub.stripe_customer_id = customer_id
            sub.stripe_subscription_id = subscription_id
            # Wait for subscription.updated for real status, but we can set pending
            db.commit()
            
    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription_obj = data.get("object", {}) if isinstance(data, dict) else getattr(data, "object", {})
        sub_id = subscription_obj.get("id") if isinstance(subscription_obj, dict) else getattr(subscription_obj, "id", None)
        customer_id = subscription_obj.get("customer") if isinstance(subscription_obj, dict) else getattr(subscription_obj, "customer", None)
        status = subscription_obj.get("status") if isinstance(subscription_obj, dict) else getattr(subscription_obj, "status", None)
        
        # We need to find the tenant by subscription_id or customer_id
        sub = db.query(TenantSubscription).filter(
            TenantSubscription.stripe_subscription_id == sub_id
        ).first()
        
        if not sub and customer_id:
            sub = db.query(TenantSubscription).filter(
                TenantSubscription.stripe_customer_id == customer_id
            ).first()
            
        if sub:
            sub.status = status
            sub.stripe_subscription_id = sub_id
            
            # Simple plan extraction, assuming one item
            items = subscription_obj.get("items", {}).get("data", []) if isinstance(subscription_obj, dict) else getattr(getattr(subscription_obj, "items", object()), "data", [])
            if items:
                first_item = items[0] if isinstance(items, list) and len(items) > 0 else None
                if first_item:
                    sub.plan_id = first_item.get("price", {}).get("id", "unknown") if isinstance(first_item, dict) else getattr(getattr(first_item, "price", object()), "id", "unknown")
                
            current_period_end = subscription_obj.get("current_period_end") if isinstance(subscription_obj, dict) else getattr(subscription_obj, "current_period_end", None)
            if current_period_end:
                sub.current_period_end = datetime.fromtimestamp(current_period_end)
                
            db.commit()

def record_usage(db: Session, tenant_id: str, event_type: str, count: int = 1):
    meter = db.query(UsageMeter).filter(
        UsageMeter.tenant_id == tenant_id,
        UsageMeter.event_type == event_type
    ).first()
    
    if not meter:
        meter = UsageMeter(id=str(uuid.uuid4()), tenant_id=tenant_id, event_type=event_type, count=count)
        db.add(meter)
    else:
        meter.count += count
    db.commit()
