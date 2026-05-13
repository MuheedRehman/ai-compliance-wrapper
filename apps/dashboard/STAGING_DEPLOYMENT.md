# Dashboard Staging Deployment

## Current Access Model

The browser authenticates to the dashboard with a signed, HTTP-only session cookie.
The browser never receives the backend API key.

Request flow:

1. User signs in at `/login` with `DASHBOARD_ADMIN_PASSWORD`.
2. The dashboard issues a signed `dashboard_session` cookie using `DASHBOARD_SESSION_SECRET`.
3. Browser API calls go to `/api/backend/...` on the dashboard service.
4. The dashboard server verifies the session cookie.
5. The dashboard server forwards the request to the backend with:
   - `x-api-key` from server-side `DASHBOARD_API_KEY`
   - Cloud Run identity token when `BACKEND_AUTH_MODE=google_id_token`

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
