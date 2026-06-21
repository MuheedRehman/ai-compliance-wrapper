"""Runtime Governance SDK routes.

Endpoints:
  POST  /v1/runtime/policy-check          — standalone policy gate (SDK use)
  GET   /v1/runtime/usage                 — per-tenant usage stats
  GET   /v1/runtime/developer-keys        — list developer (role=app) API keys
  POST  /v1/runtime/developer-keys        — create a new developer API key
  DELETE /v1/runtime/developer-keys/{key_id} — revoke a developer key
"""
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ApiKey
from app.schemas import (
    DeveloperKeyCreate,
    DeveloperKeyResponse,
    PolicyCheckRequest,
    PolicyCheckResponse,
    RuntimeUsageResponse,
)
from app.services.auth_service import DashboardPermission, authenticate_api_key
from app.services.hashing import hash_api_key
from app.services import policy_service

router = APIRouter(prefix="/v1/runtime", tags=["Runtime Governance SDK"])


# ---------------------------------------------------------------------------
# Policy check
# ---------------------------------------------------------------------------

@router.post(
    "/policy-check",
    response_model=PolicyCheckResponse,
    dependencies=[DashboardPermission("runtime:execute")],
)
def policy_check(
    payload: PolicyCheckRequest,
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="runtime:execute")
    result = policy_service.run_policy_check(
        db,
        tenant_id=auth["tenant_id"],
        api_key_id=auth.get("key_id"),
        prompt=payload.prompt,
        feature_id=payload.feature_id,
        context=payload.context,
    )
    return PolicyCheckResponse(**result)


# ---------------------------------------------------------------------------
# Usage stats
# ---------------------------------------------------------------------------

@router.get(
    "/usage",
    response_model=RuntimeUsageResponse,
    dependencies=[DashboardPermission("runtime:execute")],
)
def get_usage(
    days: int = Query(default=7, ge=1, le=90),
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="runtime:execute")
    stats = policy_service.get_usage_stats(db, auth["tenant_id"], period_days=days)
    return RuntimeUsageResponse(**stats)


# ---------------------------------------------------------------------------
# Developer keys CRUD
# ---------------------------------------------------------------------------

@router.get(
    "/developer-keys",
    response_model=list[DeveloperKeyResponse],
    dependencies=[DashboardPermission("tenant:read")],
)
def list_developer_keys(
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:read")
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == auth["tenant_id"], ApiKey.role == "app")
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return [DeveloperKeyResponse.model_validate(k) for k in keys]


@router.post(
    "/developer-keys",
    response_model=DeveloperKeyResponse,
    status_code=201,
    dependencies=[DashboardPermission("tenant:admin")],
)
def create_developer_key(
    payload: DeveloperKeyCreate,
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")

    raw_key = f"aigw_{secrets.token_hex(32)}"
    key_record = ApiKey(
        key_id=f"key-{uuid.uuid4().hex[:12]}",
        tenant_id=auth["tenant_id"],
        name=payload.name,
        description=payload.description,
        key_hash=hash_api_key(raw_key),
        role="app",
        scopes=["runtime:execute"],
        revoked=False,
    )
    db.add(key_record)
    db.commit()
    db.refresh(key_record)

    response = DeveloperKeyResponse.model_validate(key_record)
    response.raw_key = raw_key
    return response


@router.delete(
    "/developer-keys/{key_id}",
    status_code=204,
    dependencies=[DashboardPermission("tenant:admin")],
)
def revoke_developer_key(
    key_id: str,
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    auth = authenticate_api_key(db, x_api_key, required_scope="tenant:admin")
    record = (
        db.query(ApiKey)
        .filter(
            ApiKey.key_id == key_id,
            ApiKey.tenant_id == auth["tenant_id"],
            ApiKey.role == "app",
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Developer key not found.")
    if record.revoked:
        raise HTTPException(status_code=409, detail="Key is already revoked.")

    record.revoked = True
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
