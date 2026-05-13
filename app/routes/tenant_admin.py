from typing import List

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    TenantAdminSummaryResponse,
    TenantAuthPolicyResponse,
    TenantAuthPolicyUpdate,
    TenantInvitationCreate,
    TenantInvitationResponse,
    TenantLoginAuditResponse,
    TenantLoginResolveRequest,
    TenantLoginResolveResponse,
    TenantUserCreate,
    TenantUserResponse,
    TenantUserUpdate,
)
from app.services.auth_service import authenticate_api_key
from app.services import tenant_admin_service

router = APIRouter(prefix="/v1/tenant-admin", tags=["Tenant Administration"])


@router.get("/summary", response_model=TenantAdminSummaryResponse)
def get_tenant_admin_summary(
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    tenant_admin_service.require_tenant_reader(auth, x_dashboard_user_role)
    policy = tenant_admin_service.get_or_create_auth_policy(db, auth["tenant_id"])
    users = tenant_admin_service.list_users(db, auth["tenant_id"])
    invitations = tenant_admin_service.list_invitations(db, auth["tenant_id"])
    events = tenant_admin_service.list_login_events(db, auth["tenant_id"], limit=25)
    db.commit()
    return {
        "users": users,
        "invitations": invitations,
        "auth_policy": tenant_admin_service.serialize_auth_policy(policy),
        "login_events": events,
    }


@router.get("/users", response_model=List[TenantUserResponse])
def list_tenant_users(
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    tenant_admin_service.require_tenant_reader(auth, x_dashboard_user_role)
    return tenant_admin_service.list_users(db, auth["tenant_id"])


@router.post("/users", response_model=TenantUserResponse)
def create_tenant_user(
    payload: TenantUserCreate,
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    tenant_admin_service.require_tenant_admin(auth, x_dashboard_user_role)
    user = tenant_admin_service.create_user(db, auth["tenant_id"], payload.email, payload.role, payload.status, payload.name)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=TenantUserResponse)
def update_tenant_user(
    user_id: str,
    payload: TenantUserUpdate,
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    tenant_admin_service.require_tenant_admin(auth, x_dashboard_user_role)
    user = tenant_admin_service.update_user(db, auth["tenant_id"], user_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user)
    return user


@router.get("/invitations", response_model=List[TenantInvitationResponse])
def list_tenant_invitations(
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    tenant_admin_service.require_tenant_reader(auth, x_dashboard_user_role)
    return tenant_admin_service.list_invitations(db, auth["tenant_id"])


@router.post("/invitations", response_model=TenantInvitationResponse)
def invite_tenant_user(
    payload: TenantInvitationCreate,
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    x_dashboard_user_email: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    tenant_admin_service.require_tenant_admin(auth, x_dashboard_user_role)
    invitation = tenant_admin_service.invite_user(
        db,
        auth["tenant_id"],
        payload.email,
        payload.role,
        invited_by_email=x_dashboard_user_email,
    )
    db.commit()
    db.refresh(invitation)
    return invitation


@router.post("/invitations/{invitation_id}/revoke", response_model=TenantInvitationResponse)
def revoke_tenant_invitation(
    invitation_id: str,
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    tenant_admin_service.require_tenant_admin(auth, x_dashboard_user_role)
    invitation = tenant_admin_service.revoke_invitation(db, auth["tenant_id"], invitation_id)
    db.commit()
    db.refresh(invitation)
    return invitation


@router.get("/auth-policy", response_model=TenantAuthPolicyResponse)
def get_auth_policy(
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    tenant_admin_service.require_tenant_reader(auth, x_dashboard_user_role)
    policy = tenant_admin_service.get_or_create_auth_policy(db, auth["tenant_id"])
    db.commit()
    return tenant_admin_service.serialize_auth_policy(policy)


@router.patch("/auth-policy", response_model=TenantAuthPolicyResponse)
def update_auth_policy(
    payload: TenantAuthPolicyUpdate,
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    tenant_admin_service.require_tenant_admin(auth, x_dashboard_user_role)
    policy = tenant_admin_service.update_auth_policy(db, auth["tenant_id"], payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(policy)
    return tenant_admin_service.serialize_auth_policy(policy)


@router.get("/login-audit", response_model=List[TenantLoginAuditResponse])
def list_login_audit(
    limit: int = 50,
    x_api_key: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    tenant_admin_service.require_tenant_reader(auth, x_dashboard_user_role)
    return tenant_admin_service.list_login_events(db, auth["tenant_id"], limit=limit)


@router.post("/login/resolve", response_model=TenantLoginResolveResponse)
def resolve_login(
    payload: TenantLoginResolveRequest,
    x_api_key: str | None = Header(default=None),
    x_forwarded_for: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:login")
    ip_address = payload.ip_address or (x_forwarded_for.split(",")[0].strip() if x_forwarded_for else None)
    response = tenant_admin_service.resolve_login_identity(
        db,
        tenant_id=auth["tenant_id"],
        email=payload.email,
        name=payload.name,
        provider=payload.provider,
        ip_address=ip_address,
        user_agent=payload.user_agent or user_agent,
    )
    db.commit()
    return response
