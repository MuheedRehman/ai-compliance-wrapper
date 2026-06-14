from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.auth_service import authenticate_api_key, DashboardPermission
from app.schemas import (
    SubscriptionStatusResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
    EntitlementResponse
)
from app.services.billing_service import get_subscription, create_checkout, create_portal
from app.services.entitlement_service import get_entitlements
from typing import List

router = APIRouter(prefix="/v1/billing", tags=["Billing & Entitlements"])

@router.get("/subscription", response_model=SubscriptionStatusResponse)
def get_tenant_subscription(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    auth_context = authenticate_api_key(db, x_api_key, required_scope="billing")
    tenant_id = auth_context["tenant_id"]
    sub = get_subscription(db, tenant_id)
    return {
        "tenant_id": sub.tenant_id,
        "plan_id": sub.plan_id,
        "status": sub.status,
        "current_period_end": sub.current_period_end
    }

@router.post("/checkout-session", response_model=CheckoutSessionResponse, dependencies=[DashboardPermission("billing:manage")])
def create_tenant_checkout_session(
    request: CheckoutSessionRequest,
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    auth_context = authenticate_api_key(db, x_api_key, required_scope="billing")
    tenant_id = auth_context["tenant_id"]
    url = create_checkout(db, tenant_id, request.plan_id)
    return {"checkout_url": url}

@router.post("/portal-session", response_model=PortalSessionResponse, dependencies=[DashboardPermission("billing:manage")])
def create_tenant_portal_session(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    auth_context = authenticate_api_key(db, x_api_key, required_scope="billing")
    tenant_id = auth_context["tenant_id"]
    url = create_portal(db, tenant_id)
    return {"portal_url": url}

@router.get("/entitlements", response_model=List[EntitlementResponse])
def get_tenant_entitlements(
    x_api_key: str | None = Header(default=None),
    db: Session = Depends(get_db)
):
    auth_context = authenticate_api_key(db, x_api_key, required_scope="billing")
    tenant_id = auth_context["tenant_id"]
    entitlements = get_entitlements(db, tenant_id)
    return [
        {
            "feature_key": e.feature_key,
            "is_enabled": e.is_enabled,
            "limit_value": e.limit_value
        }
        for e in entitlements
    ]
