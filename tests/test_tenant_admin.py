from app.services import tenant_admin_service
from tests.conftest import TENANT_ID


def owner_session_headers(client, admin_headers, email="owner@example.com"):
    response = client.post(
        "/v1/tenant-admin/login/resolve",
        headers=admin_headers,
        json={"email": email, "name": "Owner", "provider": "google"},
    )
    assert response.status_code == 200
    user = response.json()["user"]
    return {
        **admin_headers,
        "x-dashboard-user-email": user["email"],
        "x-dashboard-user-role": user["role"],
        "x-dashboard-user-id": user["id"],
        "x-dashboard-tenant-id": TENANT_ID,
    }


def test_role_permission_matrix_separates_admin_contributor_and_read_only_access():
    owner_permissions = tenant_admin_service.permissions_for_role("owner")
    reviewer_permissions = tenant_admin_service.permissions_for_role("reviewer")
    auditor_permissions = tenant_admin_service.permissions_for_role("auditor")
    viewer_permissions = tenant_admin_service.permissions_for_role("viewer")

    assert "tenant:admin" in owner_permissions
    assert "billing:manage" in owner_permissions
    assert "governance:write" in reviewer_permissions
    assert "scanner:run" in reviewer_permissions
    assert "users:write" not in reviewer_permissions
    assert "evidence:read" in auditor_permissions
    assert "reports:write" not in auditor_permissions
    assert "governance:read" in viewer_permissions
    assert "governance:write" not in viewer_permissions
    assert tenant_admin_service.role_has_permission("viewer", "tenant:read") is True
    assert tenant_admin_service.role_has_permission("viewer", "runtime:execute") is False


def test_tenant_admin_summary_bootstraps_policy(client, admin_headers):
    response = client.get("/v1/tenant-admin/summary", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["auth_policy"]["tenant_id"] == TENANT_ID
    assert data["auth_policy"]["google_login_enabled"] is True
    assert data["users"] == []
    assert data["invitations"] == []


def test_owner_session_can_manage_users_policy_and_invitations(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)

    user_response = client.post(
        "/v1/tenant-admin/users",
        headers=owner_headers,
        json={"email": "Reviewer@Example.com", "role": "reviewer", "status": "active", "name": "Reviewer"},
    )
    assert user_response.status_code == 200
    user = user_response.json()
    assert user["email"] == "reviewer@example.com"
    assert user["role"] == "reviewer"

    update_response = client.patch(
        f"/v1/tenant-admin/users/{user['id']}",
        headers=owner_headers,
        json={"role": "auditor"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["role"] == "auditor"

    policy_response = client.patch(
        "/v1/tenant-admin/auth-policy",
        headers=owner_headers,
        json={"allowed_domains": ["Example.com"], "auto_provision_google_users": False, "default_role": "viewer"},
    )
    assert policy_response.status_code == 200
    assert policy_response.json()["allowed_domains"] == ["example.com"]

    invite_response = client.post(
        "/v1/tenant-admin/invitations",
        headers=owner_headers,
        json={"email": "Auditor@Example.com", "role": "auditor"},
    )
    assert invite_response.status_code == 200
    invitation = invite_response.json()
    assert invitation["email"] == "auditor@example.com"
    assert invitation["status"] == "pending"
    assert invitation["invited_by_email"] == "owner@example.com"

    audit_response = client.get("/v1/tenant-admin/action-audit", headers=owner_headers)
    assert audit_response.status_code == 200
    actions = audit_response.json()
    action_names = [event["action"] for event in actions]
    assert "tenant_user_created" in action_names
    assert "tenant_user_updated" in action_names
    assert "tenant_auth_policy_updated" in action_names
    assert "tenant_invitation_created" in action_names
    update_event = next(event for event in actions if event["action"] == "tenant_user_updated")
    assert update_event["before_json"]["role"] == "reviewer"
    assert update_event["after_json"]["role"] == "auditor"
    assert update_event["actor_email"] == "owner@example.com"

    summary_response = client.get("/v1/tenant-admin/summary", headers=owner_headers)
    assert summary_response.status_code == 200
    assert summary_response.json()["action_events"]


def test_viewer_session_cannot_write_tenant_admin_data(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)
    viewer = client.post(
        "/v1/tenant-admin/users",
        headers=owner_headers,
        json={"email": "viewer@example.com", "role": "viewer", "status": "active"},
    ).json()
    viewer_headers = {
        **admin_headers,
        "x-dashboard-user-email": viewer["email"],
        "x-dashboard-user-role": viewer["role"],
        "x-dashboard-user-id": viewer["id"],
        "x-dashboard-tenant-id": TENANT_ID,
    }

    response = client.post(
        "/v1/tenant-admin/users",
        headers=viewer_headers,
        json={"email": "viewer@example.com", "role": "viewer"},
    )

    assert response.status_code == 403


def test_dashboard_role_header_requires_active_tenant_user(client, admin_headers):
    spoofed_headers = {
        **admin_headers,
        "x-dashboard-user-role": "owner",
        "x-dashboard-user-email": "ghost@example.com",
        "x-dashboard-tenant-id": TENANT_ID,
    }

    response = client.post(
        "/v1/tenant-admin/users",
        headers=spoofed_headers,
        json={"email": "reviewer@example.com", "role": "reviewer"},
    )

    assert response.status_code == 403
    assert "active tenant user" in response.json()["error"]["message"].lower()


def test_dashboard_role_header_must_match_persisted_user_role(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)
    mismatched_headers = {**owner_headers, "x-dashboard-user-role": "viewer"}

    response = client.patch(
        "/v1/tenant-admin/auth-policy",
        headers=mismatched_headers,
        json={"default_role": "auditor"},
    )

    assert response.status_code == 403
    assert "does not match" in response.json()["error"]["message"].lower()


def test_dashboard_tenant_header_must_match_api_key_tenant(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)
    mismatched_headers = {**owner_headers, "x-dashboard-tenant-id": "other-tenant"}

    response = client.get("/v1/tenant-admin/users", headers=mismatched_headers)

    assert response.status_code == 403
    assert "tenant does not match" in response.json()["error"]["message"].lower()


def test_login_resolve_first_google_user_becomes_owner_and_is_audited(client, admin_headers):
    response = client.post(
        "/v1/tenant-admin/login/resolve",
        headers=admin_headers,
        json={"email": "Founder@Example.com", "name": "Founder", "provider": "google"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True
    assert data["user"]["email"] == "founder@example.com"
    assert data["user"]["role"] == "owner"
    assert "tenant:admin" in data["permissions"]

    audit_response = client.get("/v1/tenant-admin/login-audit", headers=admin_headers)
    assert audit_response.status_code == 200
    assert audit_response.json()[0]["outcome"] == "success"


def test_login_policy_blocks_unallowed_google_identity(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)
    policy_response = client.patch(
        "/v1/tenant-admin/auth-policy",
        headers=owner_headers,
        json={"allowed_domains": ["example.com"]},
    )
    assert policy_response.status_code == 200

    response = client.post(
        "/v1/tenant-admin/login/resolve",
        headers=admin_headers,
        json={"email": "blocked@other.com", "name": "Blocked", "provider": "google"},
    )

    assert response.status_code == 200
    assert response.json()["allowed"] is False
    assert response.json()["reason"] == "email_not_allowed"


def test_pending_invitation_is_accepted_on_matching_google_login(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)
    invite_response = client.post(
        "/v1/tenant-admin/invitations",
        headers=owner_headers,
        json={"email": "auditor@example.com", "role": "auditor"},
    )
    assert invite_response.status_code == 200

    response = client.post(
        "/v1/tenant-admin/login/resolve",
        headers=admin_headers,
        json={"email": "auditor@example.com", "name": "Auditor", "provider": "google"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["allowed"] is True
    assert data["user"]["role"] == "auditor"

    invitations_response = client.get("/v1/tenant-admin/invitations", headers=admin_headers)
    assert invitations_response.status_code == 200
    assert invitations_response.json()[0]["status"] == "accepted"


def test_revoke_invitation_is_action_audited(client, admin_headers):
    owner_headers = owner_session_headers(client, admin_headers)
    invite_response = client.post(
        "/v1/tenant-admin/invitations",
        headers=owner_headers,
        json={"email": "temporary@example.com", "role": "viewer"},
    )
    assert invite_response.status_code == 200
    invitation = invite_response.json()

    revoke_response = client.post(
        f"/v1/tenant-admin/invitations/{invitation['id']}/revoke",
        headers=owner_headers,
    )
    assert revoke_response.status_code == 200

    audit_response = client.get("/v1/tenant-admin/action-audit", headers=owner_headers)
    assert audit_response.status_code == 200
    revoke_event = next(event for event in audit_response.json() if event["action"] == "tenant_invitation_revoked")
    assert revoke_event["target_email"] == "temporary@example.com"
    assert revoke_event["before_json"]["status"] == "pending"
    assert revoke_event["after_json"]["status"] == "revoked"
