from dataclasses import dataclass
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


@dataclass(frozen=True)
class DashboardSessionHeaders:
    email: str | None = None
    role: str | None = None
    user_id: str | None = None
    tenant_id: str | None = None


def get_dashboard_session_headers(
    x_dashboard_user_email: str | None = Header(default=None),
    x_dashboard_user_role: str | None = Header(default=None),
    x_dashboard_user_id: str | None = Header(default=None),
    x_dashboard_tenant_id: str | None = Header(default=None),
) -> DashboardSessionHeaders:
    return DashboardSessionHeaders(
        email=x_dashboard_user_email,
        role=x_dashboard_user_role,
        user_id=x_dashboard_user_id,
        tenant_id=x_dashboard_tenant_id,
    )


def require_dashboard_reader(db: Session, auth: dict, session: DashboardSessionHeaders):
    dashboard_user = tenant_admin_service.resolve_dashboard_session_user(
        db,
        tenant_id=auth["tenant_id"],
        dashboard_email=session.email,
        dashboard_role=session.role,
        dashboard_user_id=session.user_id,
        dashboard_tenant_id=session.tenant_id,
    )
    tenant_admin_service.require_tenant_reader(auth, dashboard_user)
    return dashboard_user


def require_dashboard_admin(db: Session, auth: dict, session: DashboardSessionHeaders):
    dashboard_user = tenant_admin_service.resolve_dashboard_session_user(
        db,
        tenant_id=auth["tenant_id"],
        dashboard_email=session.email,
        dashboard_role=session.role,
        dashboard_user_id=session.user_id,
        dashboard_tenant_id=session.tenant_id,
    )
    tenant_admin_service.require_tenant_admin(auth, dashboard_user)
    return dashboard_user


@router.get("/summary", response_model=TenantAdminSummaryResponse)
def get_tenant_admin_summary(
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    require_dashboard_reader(db, auth, dashboard_session)
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
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    require_dashboard_reader(db, auth, dashboard_session)
    return tenant_admin_service.list_users(db, auth["tenant_id"])


@router.post("/users", response_model=TenantUserResponse)
def create_tenant_user(
    payload: TenantUserCreate,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    require_dashboard_admin(db, auth, dashboard_session)
    user = tenant_admin_service.create_user(db, auth["tenant_id"], payload.email, payload.role, payload.status, payload.name)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=TenantUserResponse)
def update_tenant_user(
    user_id: str,
    payload: TenantUserUpdate,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    require_dashboard_admin(db, auth, dashboard_session)
    user = tenant_admin_service.update_user(db, auth["tenant_id"], user_id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user)
    return user


@router.get("/invitations", response_model=List[TenantInvitationResponse])
def list_tenant_invitations(
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    require_dashboard_reader(db, auth, dashboard_session)
    return tenant_admin_service.list_invitations(db, auth["tenant_id"])


@router.post("/invitations", response_model=TenantInvitationResponse)
def invite_tenant_user(
    payload: TenantInvitationCreate,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    dashboard_user = require_dashboard_admin(db, auth, dashboard_session)
    invitation = tenant_admin_service.invite_user(
        db,
        auth["tenant_id"],
        payload.email,
        payload.role,
        invited_by_email=dashboard_user.email if dashboard_user else None,
    )
    db.commit()
    db.refresh(invitation)
    return invitation


@router.post("/invitations/{invitation_id}/revoke", response_model=TenantInvitationResponse)
def revoke_tenant_invitation(
    invitation_id: str,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    require_dashboard_admin(db, auth, dashboard_session)
    invitation = tenant_admin_service.revoke_invitation(db, auth["tenant_id"], invitation_id)
    db.commit()
    db.refresh(invitation)
    return invitation


@router.get("/auth-policy", response_model=TenantAuthPolicyResponse)
def get_auth_policy(
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    require_dashboard_reader(db, auth, dashboard_session)
    policy = tenant_admin_service.get_or_create_auth_policy(db, auth["tenant_id"])
    db.commit()
    return tenant_admin_service.serialize_auth_policy(policy)


@router.patch("/auth-policy", response_model=TenantAuthPolicyResponse)
def update_auth_policy(
    payload: TenantAuthPolicyUpdate,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    require_dashboard_admin(db, auth, dashboard_session)
    policy = tenant_admin_service.update_auth_policy(db, auth["tenant_id"], payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(policy)
    return tenant_admin_service.serialize_auth_policy(policy)


@router.get("/login-audit", response_model=List[TenantLoginAuditResponse])
def list_login_audit(
    limit: int = 50,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    require_dashboard_reader(db, auth, dashboard_session)
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
