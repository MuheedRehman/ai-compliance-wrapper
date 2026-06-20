"""
Route-level DashboardPermission tests.

Pattern under test:
  - x-dashboard-user-role header absent  → role resolved from API key DB record; same gate applied
  - x-dashboard-user-role: viewer        → 403 on any write endpoint (viewer lacks *:write perms)
  - x-dashboard-user-role: auditor       → 403 on write endpoints (auditor = read-only)
  - x-dashboard-user-role: reviewer      → 403 on billing:manage (reviewer lacks that perm)
  - x-dashboard-user-role: owner         → passes RBAC gate (may still fail scope/body validation)
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _viewer_headers(base: dict) -> dict:
    return {**base, "x-dashboard-user-role": "viewer"}

def _auditor_headers(base: dict) -> dict:
    return {**base, "x-dashboard-user-role": "auditor"}

def _reviewer_headers(base: dict) -> dict:
    return {**base, "x-dashboard-user-role": "reviewer"}

def _owner_headers(base: dict) -> dict:
    return {**base, "x-dashboard-user-role": "owner"}


# ---------------------------------------------------------------------------
# Viewer is blocked on every write-permission category
# ---------------------------------------------------------------------------

def test_viewer_blocked_governance_write_ai_systems(client: TestClient, admin_headers):
    res = client.post("/v1/ai-systems", json={"name": "x"}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403
    body = res.text
    assert "governance:write" in body


def test_viewer_blocked_governance_write_compliance(client: TestClient, admin_headers):
    res = client.post("/v1/compliance/controls", json={}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403


def test_viewer_blocked_evidence_write(client: TestClient, admin_headers):
    res = client.post("/v1/evidence/items", json={}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403
    assert "evidence:write" in res.text


def test_viewer_blocked_reports_write(client: TestClient, admin_headers):
    res = client.post("/v1/reports", json={}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403
    assert "reports:write" in res.text


def test_viewer_blocked_scanner_run(client: TestClient, admin_headers):
    res = client.post("/v1/website-scans", json={"url": "https://example.com"}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403
    assert "scanner:run" in res.text


def test_viewer_blocked_fria_create(client: TestClient, admin_headers):
    res = client.post("/v1/obligations/fria", json={}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403


def test_viewer_blocked_intake_create(client: TestClient, admin_headers):
    res = client.post("/v1/intake", json={}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403


def test_viewer_blocked_feature_create(client: TestClient, admin_headers):
    res = client.post("/v1/features", json={}, headers=_viewer_headers(admin_headers))
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Auditor is read-only — blocked on write
# ---------------------------------------------------------------------------

def test_auditor_blocked_governance_write(client: TestClient, admin_headers):
    res = client.post("/v1/ai-systems", json={"name": "x"}, headers=_auditor_headers(admin_headers))
    assert res.status_code == 403


def test_auditor_blocked_evidence_write(client: TestClient, admin_headers):
    res = client.post("/v1/evidence/items", json={}, headers=_auditor_headers(admin_headers))
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Reviewer lacks billing:manage
# ---------------------------------------------------------------------------

def test_reviewer_blocked_billing_manage(client: TestClient, admin_headers):
    res = client.post("/v1/billing/checkout-session", json={"plan_id": "pro"}, headers=_reviewer_headers(admin_headers))
    assert res.status_code == 403
    assert "billing:manage" in res.text


def test_reviewer_blocked_runtime_execute(client: TestClient, admin_headers):
    res = client.post("/v1/chat/completions", json={}, headers=_reviewer_headers(admin_headers))
    assert res.status_code == 403
    assert "runtime:execute" in res.text


# ---------------------------------------------------------------------------
# Owner passes RBAC gate (subsequent failure is scope/body, not 403 from RBAC)
# ---------------------------------------------------------------------------

def test_owner_passes_rbac_on_governance_write(client: TestClient, admin_headers):
    """Owner has governance:write — RBAC gate passes. 422 from missing body is expected."""
    res = client.post("/v1/ai-systems", json={}, headers=_owner_headers(admin_headers))
    assert res.status_code != 403


def test_owner_passes_rbac_on_evidence_write(client: TestClient, admin_headers):
    res = client.post("/v1/evidence/items", json={}, headers=_owner_headers(admin_headers))
    assert res.status_code != 403


def test_owner_passes_rbac_on_reports_write(client: TestClient, admin_headers):
    res = client.post("/v1/reports", json={}, headers=_owner_headers(admin_headers))
    assert res.status_code != 403


def test_owner_passes_rbac_on_billing_manage(client: TestClient, admin_headers):
    res = client.post("/v1/billing/checkout-session", json={"plan_id": "pro"}, headers=_owner_headers(admin_headers))
    assert res.status_code != 403


def test_owner_passes_rbac_on_runtime_execute(client: TestClient, admin_headers):
    res = client.post("/v1/chat/completions", json={}, headers=_owner_headers(admin_headers))
    assert res.status_code != 403


# ---------------------------------------------------------------------------
# No dashboard header — role resolved from API key record; gate still applied
# ---------------------------------------------------------------------------

def test_direct_api_key_role_checked_when_no_dashboard_header(client: TestClient, admin_headers):
    """Without x-dashboard-user-role, DashboardPermission resolves role from the API key's
    DB record. The test admin key (role='admin') has all permissions so the gate passes."""
    res = client.post("/v1/ai-systems", json={}, headers=admin_headers)
    assert res.status_code != 403


def test_direct_auditor_api_key_blocked_on_governance_write(client: TestClient, db_session):
    """API key with role='auditor' must not write governance even without a role header.
    Giving it 'admin' scope proves the block comes from RBAC, not scope enforcement."""
    from app.models import ApiKey
    from app.services.hashing import hash_api_key

    raw_key = "aigw_test_auditor_rbac_direct_key"
    db_session.add(ApiKey(
        key_id="test-auditor-rbac-direct",
        tenant_id="tenant_test",
        name="Auditor RBAC Direct Key",
        key_hash=hash_api_key(raw_key),
        role="auditor",
        scopes=["admin"],  # full scopes so authenticate_api_key never fires first
        revoked=False,
    ))
    db_session.commit()

    headers = {"x-api-key": raw_key}

    res = client.post("/v1/ai-systems", json={"name": "blocked"}, headers=headers)
    assert res.status_code == 403
    assert "governance:write" in res.text
