from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sqlalchemy import text

from app.models import TenantActionAudit, TenantAuthPolicy, TenantInvitation, TenantLoginAudit, TenantUser


TENANT_ROLES = {"owner", "admin", "reviewer", "auditor", "viewer"}
ADMIN_ROLES = {"owner", "admin"}
READ_ROLES = TENANT_ROLES
TENANT_USER_STATUSES = {"active", "invited", "disabled"}
INVITATION_STATUSES = {"pending", "accepted", "revoked", "expired"}

ROLE_PERMISSIONS = {
    "owner": [
        "tenant:read",
        "tenant:admin",
        "users:write",
        "policy:write",
        "billing:manage",
        "governance:read",
        "governance:review",
        "governance:write",
        "evidence:read",
        "evidence:write",
        "reports:read",
        "reports:write",
        "scanner:run",
        "runtime:execute",
    ],
    "admin": [
        "tenant:read",
        "tenant:admin",
        "users:write",
        "policy:write",
        "billing:manage",
        "governance:read",
        "governance:review",
        "governance:write",
        "evidence:read",
        "evidence:write",
        "reports:read",
        "reports:write",
        "scanner:run",
        "runtime:execute",
    ],
    "reviewer": [
        "tenant:read",
        "governance:read",
        "governance:review",
        "governance:write",
        "evidence:read",
        "evidence:write",
        "reports:read",
        "reports:write",
        "scanner:run",
    ],
    "auditor": ["tenant:read", "governance:read", "evidence:read", "reports:read"],
    "viewer": ["tenant:read", "governance:read", "evidence:read", "reports:read"],
}


def normalize_email(email: str) -> str:
    cleaned = (email or "").strip().lower()
    if "@" not in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
        raise HTTPException(status_code=400, detail="Invalid email address")
    return cleaned


def normalize_domains(domains: list[str] | None) -> list[str]:
    normalized = []
    for domain in domains or []:
        value = domain.strip().lower().removeprefix("@")
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def normalize_emails(emails: list[str] | None) -> list[str]:
    normalized = []
    for email in emails or []:
        value = normalize_email(email)
        if value not in normalized:
            normalized.append(value)
    return normalized


def permissions_for_role(role: str) -> list[str]:
    return list(ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"]))


def role_has_permission(role: str, permission: str) -> bool:
    return permission in permissions_for_role(role)


def resolve_dashboard_session_user(
    db: Session,
    tenant_id: str,
    dashboard_email: str | None = None,
    dashboard_role: str | None = None,
    dashboard_user_id: str | None = None,
    dashboard_tenant_id: str | None = None,
) -> TenantUser | None:
    has_dashboard_claim = any([dashboard_email, dashboard_role, dashboard_user_id, dashboard_tenant_id])
    if not has_dashboard_claim:
        return None

    if dashboard_tenant_id and dashboard_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Dashboard tenant does not match API key tenant")

    normalized_role = (dashboard_role or "").strip().lower()
    if normalized_role not in TENANT_ROLES:
        raise HTTPException(status_code=403, detail="Valid dashboard user role is required")

    normalized_email = normalize_email(dashboard_email) if dashboard_email else None
    if not normalized_email and not dashboard_user_id:
        raise HTTPException(status_code=403, detail="Dashboard user identity is required")

    query = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id)
    if dashboard_user_id:
        query = query.filter(TenantUser.id == dashboard_user_id)
    if normalized_email:
        query = query.filter(TenantUser.email == normalized_email)

    user = query.first()
    if not user or user.status != "active":
        raise HTTPException(status_code=403, detail="Active tenant user session is required")
    if user.role != normalized_role:
        raise HTTPException(status_code=403, detail="Dashboard role does not match tenant user")
    return user


def require_tenant_reader(auth: dict, dashboard_user: TenantUser | None = None) -> None:
    if auth.get("role") == "admin" and not dashboard_user:
        return
    if dashboard_user and dashboard_user.role in READ_ROLES:
        return
    raise HTTPException(status_code=403, detail="Tenant user session is required")


def require_tenant_admin(auth: dict, dashboard_user: TenantUser | None = None) -> None:
    if auth.get("role") == "admin" and not dashboard_user:
        return
    if dashboard_user and dashboard_user.role in ADMIN_ROLES:
        return
    raise HTTPException(status_code=403, detail="Tenant administrator role is required")


def get_or_create_auth_policy(db: Session, tenant_id: str) -> TenantAuthPolicy:
    policy = db.get(TenantAuthPolicy, tenant_id)
    if policy:
        return policy

    policy = TenantAuthPolicy(tenant_id=tenant_id)
    db.add(policy)
    db.flush()
    return policy


def serialize_auth_policy(policy: TenantAuthPolicy) -> dict:
    return {
        "tenant_id": policy.tenant_id,
        "google_login_enabled": bool(policy.google_login_enabled),
        "password_login_enabled": bool(policy.password_login_enabled),
        "allowed_domains": list(policy.allowed_domains_json or []),
        "allowed_emails": list(policy.allowed_emails_json or []),
        "auto_provision_google_users": bool(policy.auto_provision_google_users),
        "default_role": policy.default_role,
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
    }


def serialize_user(user: TenantUser) -> dict:
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "status": user.status,
        "auth_provider": user.auth_provider,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


def serialize_invitation(invitation: TenantInvitation) -> dict:
    return {
        "id": invitation.id,
        "tenant_id": invitation.tenant_id,
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "invited_by_email": invitation.invited_by_email,
        "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
    }


def list_users(db: Session, tenant_id: str) -> list[TenantUser]:
    return (
        db.query(TenantUser)
        .filter(TenantUser.tenant_id == tenant_id)
        .order_by(TenantUser.created_at.asc(), TenantUser.email.asc())
        .all()
    )


def list_invitations(db: Session, tenant_id: str) -> list[TenantInvitation]:
    return (
        db.query(TenantInvitation)
        .filter(TenantInvitation.tenant_id == tenant_id)
        .order_by(TenantInvitation.created_at.desc())
        .all()
    )


def list_login_events(db: Session, tenant_id: str, limit: int = 50) -> list[TenantLoginAudit]:
    safe_limit = min(max(limit, 1), 200)
    return (
        db.query(TenantLoginAudit)
        .filter(TenantLoginAudit.tenant_id == tenant_id)
        .order_by(TenantLoginAudit.created_at.desc())
        .limit(safe_limit)
        .all()
    )


def list_action_events(db: Session, tenant_id: str, limit: int = 50) -> list[TenantActionAudit]:
    safe_limit = min(max(limit, 1), 200)
    return (
        db.query(TenantActionAudit)
        .filter(TenantActionAudit.tenant_id == tenant_id)
        .order_by(TenantActionAudit.created_at.desc())
        .limit(safe_limit)
        .all()
    )


def get_user(db: Session, tenant_id: str, user_id: str) -> TenantUser:
    user = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id, TenantUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Tenant user not found")
    return user


def get_invitation(db: Session, tenant_id: str, invitation_id: str) -> TenantInvitation:
    invitation = (
        db.query(TenantInvitation)
        .filter(TenantInvitation.tenant_id == tenant_id, TenantInvitation.id == invitation_id)
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Tenant invitation not found")
    return invitation


def _find_pending_invitation(db: Session, tenant_id: str, email: str) -> TenantInvitation | None:
    return (
        db.query(TenantInvitation)
        .filter(
            TenantInvitation.tenant_id == tenant_id,
            TenantInvitation.email == email,
            TenantInvitation.status == "pending",
        )
        .order_by(TenantInvitation.created_at.desc())
        .first()
    )


def _active_owner_count(db: Session, tenant_id: str, exclude_user_id: str | None = None) -> int:
    query = db.query(TenantUser).filter(
        TenantUser.tenant_id == tenant_id,
        TenantUser.role == "owner",
        TenantUser.status == "active",
    )
    if exclude_user_id:
        query = query.filter(TenantUser.id != exclude_user_id)
    return query.count()


def _ensure_not_last_owner(db: Session, user: TenantUser, next_role: str, next_status: str) -> None:
    removing_owner = user.role == "owner" and (next_role != "owner" or next_status != "active")
    if removing_owner and _active_owner_count(db, user.tenant_id, exclude_user_id=user.id) == 0:
        raise HTTPException(status_code=400, detail="At least one active owner is required")


def create_user(db: Session, tenant_id: str, email: str, role: str, status: str, name: str | None) -> TenantUser:
    email = normalize_email(email)
    existing = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id, TenantUser.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tenant user already exists")
    if role not in TENANT_ROLES:
        raise HTTPException(status_code=400, detail="Invalid tenant role")
    if status not in TENANT_USER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid tenant user status")

    user = TenantUser(
        id=f"usr_{uuid4().hex}",
        tenant_id=tenant_id,
        email=email,
        name=name,
        role=role,
        status=status,
        auth_provider="manual",
    )
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, tenant_id: str, user_id: str, changes: dict) -> TenantUser:
    user = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id, TenantUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Tenant user not found")

    next_role = changes.get("role") or user.role
    next_status = changes.get("status") or user.status
    if next_role not in TENANT_ROLES:
        raise HTTPException(status_code=400, detail="Invalid tenant role")
    if next_status not in TENANT_USER_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid tenant user status")

    _ensure_not_last_owner(db, user, next_role, next_status)

    if "name" in changes:
        user.name = changes["name"]
    if "role" in changes:
        user.role = next_role
    if "status" in changes:
        user.status = next_status
    db.flush()
    return user


def invite_user(
    db: Session,
    tenant_id: str,
    email: str,
    role: str,
    invited_by_email: str | None = None,
) -> TenantInvitation:
    email = normalize_email(email)
    if role not in TENANT_ROLES:
        raise HTTPException(status_code=400, detail="Invalid tenant role")

    existing_user = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id, TenantUser.email == email).first()
    if existing_user and existing_user.status != "disabled":
        raise HTTPException(status_code=409, detail="Tenant user already exists")

    invitation = _find_pending_invitation(db, tenant_id, email)
    if invitation:
        invitation.role = role
        invitation.invited_by_email = invited_by_email or invitation.invited_by_email
        db.flush()
        return invitation

    invitation = TenantInvitation(
        id=f"inv_{uuid4().hex}",
        tenant_id=tenant_id,
        email=email,
        role=role,
        status="pending",
        invited_by_email=invited_by_email,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    db.flush()
    return invitation


def revoke_invitation(db: Session, tenant_id: str, invitation_id: str) -> TenantInvitation:
    invitation = (
        db.query(TenantInvitation)
        .filter(TenantInvitation.tenant_id == tenant_id, TenantInvitation.id == invitation_id)
        .first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Tenant invitation not found")
    if invitation.status == "pending":
        invitation.status = "revoked"
        db.flush()
    return invitation


def update_auth_policy(db: Session, tenant_id: str, changes: dict) -> TenantAuthPolicy:
    policy = get_or_create_auth_policy(db, tenant_id)

    if "google_login_enabled" in changes:
        policy.google_login_enabled = bool(changes["google_login_enabled"])
    if "password_login_enabled" in changes:
        policy.password_login_enabled = bool(changes["password_login_enabled"])
    if "allowed_domains" in changes:
        policy.allowed_domains_json = normalize_domains(changes["allowed_domains"])
    if "allowed_emails" in changes:
        policy.allowed_emails_json = normalize_emails(changes["allowed_emails"])
    if "auto_provision_google_users" in changes:
        policy.auto_provision_google_users = bool(changes["auto_provision_google_users"])
    if "default_role" in changes:
        default_role = changes["default_role"]
        if default_role not in TENANT_ROLES or default_role == "owner":
            raise HTTPException(status_code=400, detail="Default role must be admin, reviewer, auditor, or viewer")
        policy.default_role = default_role

    db.flush()
    return policy


def record_login_event(
    db: Session,
    tenant_id: str | None,
    email: str | None,
    provider: str,
    outcome: str,
    reason: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TenantLoginAudit:
    event = TenantLoginAudit(
        id=f"log_{uuid4().hex}",
        tenant_id=tenant_id,
        email=email,
        provider=provider,
        outcome=outcome,
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    db.flush()
    return event


def record_action_event(
    db: Session,
    tenant_id: str,
    action: str,
    target_type: str,
    target_id: str | None = None,
    target_email: str | None = None,
    actor_user: TenantUser | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    metadata: dict | None = None,
) -> TenantActionAudit:
    event = TenantActionAudit(
        id=f"act_{uuid4().hex}",
        tenant_id=tenant_id,
        actor_user_id=actor_user.id if actor_user else None,
        actor_email=actor_user.email if actor_user else actor_email,
        actor_role=actor_user.role if actor_user else actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_email=target_email,
        before_json=jsonable_encoder(before) if before is not None else None,
        after_json=jsonable_encoder(after) if after is not None else None,
        metadata_json=jsonable_encoder(metadata or {}),
    )
    db.add(event)
    db.flush()
    return event


def _is_email_allowed_by_policy(policy: TenantAuthPolicy, email: str) -> bool:
    allowed_domains = set(policy.allowed_domains_json or [])
    allowed_emails = set(policy.allowed_emails_json or [])
    if not allowed_domains and not allowed_emails:
        return True
    domain = email.split("@", 1)[1]
    return email in allowed_emails or domain in allowed_domains


def _failure(
    db: Session,
    tenant_id: str,
    email: str,
    provider: str,
    reason: str,
    ip_address: str | None,
    user_agent: str | None,
) -> dict:
    record_login_event(db, tenant_id, email, provider, "failure", reason, ip_address, user_agent)
    return {"allowed": False, "reason": reason, "tenant_id": tenant_id, "user": None, "permissions": []}


def resolve_login_identity(
    db: Session,
    tenant_id: str,
    email: str,
    name: str | None,
    provider: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    email = normalize_email(email)
    policy = get_or_create_auth_policy(db, tenant_id)

    if provider == "google" and not policy.google_login_enabled:
        return _failure(db, tenant_id, email, provider, "google_login_disabled", ip_address, user_agent)
    if provider == "password" and not policy.password_login_enabled:
        return _failure(db, tenant_id, email, provider, "password_login_disabled", ip_address, user_agent)
    if not _is_email_allowed_by_policy(policy, email):
        return _failure(db, tenant_id, email, provider, "email_not_allowed", ip_address, user_agent)

    now = datetime.now(timezone.utc)
    user = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id, TenantUser.email == email).first()
    if user:
        if user.status == "disabled":
            return _failure(db, tenant_id, email, provider, "user_disabled", ip_address, user_agent)
        user.status = "active"
        user.name = name or user.name
        user.auth_provider = provider
        user.last_login_at = now
        record_login_event(db, tenant_id, email, provider, "success", None, ip_address, user_agent)
        db.flush()
        return {
            "allowed": True,
            "reason": None,
            "tenant_id": tenant_id,
            "user": user,
            "permissions": permissions_for_role(user.role),
        }

    invitation = _find_pending_invitation(db, tenant_id, email)
    if invitation:
        inv_expires = invitation.expires_at
        if inv_expires:
            # SQLite returns naive datetimes; Postgres returns aware — normalize before compare
            if inv_expires.tzinfo is None:
                inv_expires = inv_expires.replace(tzinfo=timezone.utc)
            if inv_expires < now:
                invitation.status = "expired"
                return _failure(db, tenant_id, email, provider, "invitation_expired", ip_address, user_agent)
        user = TenantUser(
            id=f"usr_{uuid4().hex}",
            tenant_id=tenant_id,
            email=email,
            name=name,
            role=invitation.role,
            status="active",
            auth_provider=provider,
            last_login_at=now,
        )
        invitation.status = "accepted"
        invitation.accepted_at = now
        db.add(user)
        record_login_event(db, tenant_id, email, provider, "success", None, ip_address, user_agent)
        db.flush()
        return {
            "allowed": True,
            "reason": None,
            "tenant_id": tenant_id,
            "user": user,
            "permissions": permissions_for_role(user.role),
        }

    has_users = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).count() > 0
    if not has_users:
        role = "owner"
    elif policy.auto_provision_google_users:
        role = policy.default_role
    else:
        return _failure(db, tenant_id, email, provider, "user_not_invited", ip_address, user_agent)

    user = TenantUser(
        id=f"usr_{uuid4().hex}",
        tenant_id=tenant_id,
        email=email,
        name=name,
        role=role,
        status="active",
        auth_provider=provider,
        last_login_at=now,
    )
    db.add(user)
    record_login_event(db, tenant_id, email, provider, "success", None, ip_address, user_agent)
    db.flush()
    return {
        "allowed": True,
        "reason": None,
        "tenant_id": tenant_id,
        "user": user,
        "permissions": permissions_for_role(user.role),
    }


def purge_tenant(db: Session, tenant_id: str) -> dict:
    """GDPR Right to Erasure — hard-deletes all data belonging to a tenant.
    Deletes in FK-dependency order so no constraint violations occur.
    This operation is irreversible."""
    tables_in_order = [
        # Leaf tables first (no dependants)
        "evidence_artifacts",
        "evidence_items",
        "evidence_logs",
        "control_review_events",
        "compliance_controls",
        "ai_system_review_events",
        "fria_records",
        "oversight_assignments",
        "incidents",
        "website_scans",
        "ai_system_intakes",
        "reports",
        "ai_feature_versions",
        "ai_features",
        "ai_systems",
        "usage_meters",
        "entitlements",
        "tenant_subscriptions",
        "tenant_action_audit",
        "tenant_login_audit",
        "tenant_invitations",
        "tenant_users",
        "tenant_auth_policies",
        "api_keys",
    ]
    counts: dict[str, int] = {}
    for table in tables_in_order:
        result = db.execute(
            text(f"DELETE FROM {table} WHERE tenant_id = :tid"),
            {"tid": tenant_id},
        )
        counts[table] = result.rowcount

    # Delete the tenant record last
    result = db.execute(
        text("DELETE FROM tenants WHERE tenant_id = :tid"),
        {"tid": tenant_id},
    )
    counts["tenants"] = result.rowcount
    db.commit()
    return counts
