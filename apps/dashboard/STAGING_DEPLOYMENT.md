# Dashboard Staging Deployment

## Current Access Model

The browser authenticates to the dashboard with a signed, HTTP-only session cookie.
The browser never receives the backend API key.

Request flow:

1. User signs in at `/login` with `DASHBOARD_ADMIN_PASSWORD`.
2. The dashboard resolves the password owner through `/v1/tenant-admin/login/resolve`.
3. The dashboard issues a signed `dashboard_session` cookie using the backend tenant user id, email, and role.
4. Browser API calls go to `/api/backend/...` on the dashboard service.
5. The dashboard server verifies the session cookie.
6. The dashboard server checks the session role against the requested backend path and method.
7. The dashboard server forwards allowed requests to the backend with:
   - `x-api-key` from server-side `DASHBOARD_API_KEY`
   - `x-dashboard-user-id`, `x-dashboard-user-email`, `x-dashboard-user-role`, and `x-dashboard-tenant-id`
   - Cloud Run identity token when `BACKEND_AUTH_MODE=google_id_token`

The backend only accepts dashboard role headers when they match an active
tenant user for the API-key tenant.

Dashboard role permissions:

- Owner/Admin: tenant administration, billing, governance writes, evidence writes, reports, scanner runs, and runtime execution.
- Reviewer: governance/evidence/report contributor access and scanner runs, without tenant administration or billing access.
- Auditor/Viewer: read-only governance, evidence, and report access.

## Required Dashboard Runtime Secrets

- `DASHBOARD_API_KEY`
- `DASHBOARD_ADMIN_PASSWORD`
- `DASHBOARD_SESSION_SECRET`

## Required Dashboard Runtime Environment

- `BACKEND_URL`
- `BACKEND_AUTH_MODE=google_id_token` for Cloud Run staging

## Cloud Run Access

The dashboard may stay public for staging sign-in, but the backend should not grant
`roles/run.invoker` to `allUsers`. The backend should grant `roles/run.invoker`
only to the dashboard runtime service account.

## E2E Gate

Cloud Build runs the dashboard Playwright suite after deployment. Deployments fail
if the live product smoke tests fail.
