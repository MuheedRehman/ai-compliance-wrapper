from dataclasses import dataclass
from typing import List

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.db import get_db
from fastapi import Query

from app.schemas import (
    TenantAdminSummaryResponse,
    TenantActionAuditResponse,
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
from app.limiter import limiter
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


def record_tenant_action(
    db: Session,
    auth: dict,
    dashboard_user,
    action: str,
    target_type: str,
    target_id: str | None = None,
    target_email: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    metadata: dict | None = None,
):
    return tenant_admin_service.record_action_event(
        db,
        tenant_id=auth["tenant_id"],
        actor_user=dashboard_user,
        actor_email=None if dashboard_user else auth.get("key_name"),
        actor_role=None if dashboard_user else auth.get("role"),
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_email=target_email,
        before=before,
        after=after,
        metadata={
            "key_id": auth.get("key_id"),
            "key_name": auth.get("key_name"),
            **(metadata or {}),
        },
    )


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
    action_events = tenant_admin_service.list_action_events(db, auth["tenant_id"], limit=25)
    db.commit()
    return {
        "users": users,
        "invitations": invitations,
        "auth_policy": tenant_admin_service.serialize_auth_policy(policy),
        "login_events": events,
        "action_events": action_events,
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
    dashboard_user = require_dashboard_admin(db, auth, dashboard_session)
    user = tenant_admin_service.create_user(db, auth["tenant_id"], payload.email, payload.role, payload.status, payload.name)
    record_tenant_action(
        db,
        auth,
        dashboard_user,
        action="tenant_user_created",
        target_type="tenant_user",
        target_id=user.id,
        target_email=user.email,
        after=tenant_admin_service.serialize_user(user),
    )
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
    dashboard_user = require_dashboard_admin(db, auth, dashboard_session)
    existing_user = tenant_admin_service.get_user(db, auth["tenant_id"], user_id)
    before = tenant_admin_service.serialize_user(existing_user)
    user = tenant_admin_service.update_user(db, auth["tenant_id"], user_id, payload.model_dump(exclude_unset=True))
    record_tenant_action(
        db,
        auth,
        dashboard_user,
        action="tenant_user_updated",
        target_type="tenant_user",
        target_id=user.id,
        target_email=user.email,
        before=before,
        after=tenant_admin_service.serialize_user(user),
    )
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
    record_tenant_action(
        db,
        auth,
        dashboard_user,
        action="tenant_invitation_created",
        target_type="tenant_invitation",
        target_id=invitation.id,
        target_email=invitation.email,
        after=tenant_admin_service.serialize_invitation(invitation),
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
    dashboard_user = require_dashboard_admin(db, auth, dashboard_session)
    existing_invitation = tenant_admin_service.get_invitation(db, auth["tenant_id"], invitation_id)
    before = tenant_admin_service.serialize_invitation(existing_invitation)
    invitation = tenant_admin_service.revoke_invitation(db, auth["tenant_id"], invitation_id)
    record_tenant_action(
        db,
        auth,
        dashboard_user,
        action="tenant_invitation_revoked",
        target_type="tenant_invitation",
        target_id=invitation.id,
        target_email=invitation.email,
        before=before,
        after=tenant_admin_service.serialize_invitation(invitation),
    )
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
    dashboard_user = require_dashboard_admin(db, auth, dashboard_session)
    existing_policy = tenant_admin_service.get_or_create_auth_policy(db, auth["tenant_id"])
    before = tenant_admin_service.serialize_auth_policy(existing_policy)
    policy = tenant_admin_service.update_auth_policy(db, auth["tenant_id"], payload.model_dump(exclude_unset=True))
    record_tenant_action(
        db,
        auth,
        dashboard_user,
        action="tenant_auth_policy_updated",
        target_type="tenant_auth_policy",
        target_id=policy.tenant_id,
        before=before,
        after=tenant_admin_service.serialize_auth_policy(policy),
    )
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


@router.get("/action-audit", response_model=List[TenantActionAuditResponse])
def list_action_audit(
    limit: int = 50,
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    require_dashboard_reader(db, auth, dashboard_session)
    return tenant_admin_service.list_action_events(db, auth["tenant_id"], limit=limit)


@router.post("/login/resolve", response_model=TenantLoginResolveResponse)
@limiter.limit("10/minute")
def resolve_login(
    request: Request,
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


@router.delete("/data", status_code=204, summary="GDPR Right to Erasure — purge all tenant data")
def purge_tenant_data(
    confirm: str = Query(..., description="Must be the string 'DELETE_ALL_DATA' to confirm"),
    x_api_key: str | None = Header(default=None),
    dashboard_session: DashboardSessionHeaders = Depends(get_dashboard_session_headers),
    db: Session = Depends(get_db),
):
    """Permanently deletes all data associated with this tenant (GDPR Art. 17).
    Requires tenant:admin scope and owner/admin dashboard role. Irreversible."""
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    require_dashboard_admin(db, auth, dashboard_session)
    if confirm != "DELETE_ALL_DATA":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Confirmation string must be exactly 'DELETE_ALL_DATA'",
        )
    tenant_admin_service.purge_tenant(db, auth["tenant_id"])
