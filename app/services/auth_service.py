from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.models import ApiKey
from app.services.hashing import hash_api_key


def authenticate_api_key(db: Session, api_key: str | None, required_scope: str) -> dict:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_hash = hash_api_key(api_key)
    record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()

    if not record or record.revoked:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    scopes = record.scopes or []

    if required_scope not in scopes and "admin" not in scopes:
        raise HTTPException(status_code=403, detail=f"Missing required scope: {required_scope}")

    record.last_used_at = datetime.now(timezone.utc)
    db.flush()

    return {
        "key_id": record.key_id,
        "tenant_id": record.tenant_id,
        "role": record.role,
        "scopes": scopes,
        "key_hash": key_hash,
        "key_name": record.name,
    }


# --- Dashboard session role enforcement ---
# Mirrors the ROLE_PERMISSIONS matrix in tenant_admin_service.py.
# When a request arrives through the dashboard proxy it carries
# x-dashboard-user-role; we enforce the same permission gate here so that
# the backend is authoritative even if the proxy check is bypassed.

_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "owner": [
        "tenant:read", "tenant:admin", "users:write", "policy:write",
        "billing:manage", "governance:read", "governance:review",
        "governance:write", "evidence:read", "evidence:write",
        "reports:read", "reports:write", "scanner:run", "runtime:execute",
    ],
    "admin": [
        "tenant:read", "tenant:admin", "users:write", "policy:write",
        "billing:manage", "governance:read", "governance:review",
        "governance:write", "evidence:read", "evidence:write",
        "reports:read", "reports:write", "scanner:run", "runtime:execute",
    ],
    "reviewer": [
        "tenant:read", "governance:read", "governance:review",
        "governance:write", "evidence:read", "evidence:write",
        "reports:read", "reports:write", "scanner:run",
    ],
    "auditor": ["tenant:read", "governance:read", "evidence:read", "reports:read"],
    "viewer":  ["tenant:read", "governance:read", "evidence:read", "reports:read"],
}


def DashboardPermission(required_permission: str):
    """
    FastAPI dependency factory. When the request carries x-dashboard-user-role
    (set by the dashboard proxy), verify the role has required_permission.
    If the header is absent the request is a direct API key call — governed by
    scopes alone, no additional check applied.
    """
    def _check(x_dashboard_user_role: str | None = Header(default=None)) -> None:
        if x_dashboard_user_role is None:
            return
        allowed = required_permission in _ROLE_PERMISSIONS.get(x_dashboard_user_role, [])
        if not allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Dashboard role '{x_dashboard_user_role}' does not have permission '{required_permission}'",
            )
    return Depends(_check)
