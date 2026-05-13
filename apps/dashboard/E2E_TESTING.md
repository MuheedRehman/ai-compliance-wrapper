# Dashboard E2E Testing

The dashboard has a Playwright product smoke suite that covers:

- API preflight checks for the core backend endpoints.
- Main navigation rendering and visible error detection.
- Critical create flows for systems, features, scanner, controls, intake, oversight, incidents, reports, and governed runtime.

Staging routes browser API calls through the dashboard server. The dashboard service verifies an HTTP-only signed session cookie, reads `DASHBOARD_API_KEY` from Secret Manager, and forwards requests to the backend without exposing the key in browser JavaScript. The backend is invoked service-to-service with a Cloud Run identity token.

## Local

Start the backend and dashboard, then run:

```powershell
$env:DASHBOARD_PASSWORD = "<dashboard password>"
npm run e2e
```

If you want Playwright to start the dashboard dev server:

```powershell
$env:E2E_START_SERVER = "1"
$env:DASHBOARD_PASSWORD = "<dashboard password>"
npm run e2e
```

## Staging

```powershell
$env:DASHBOARD_URL = "https://ai-compliance-dashboard-loilav7ubq-ey.a.run.app"
$env:DASHBOARD_PASSWORD = "<staging dashboard password>"
npm run e2e:staging
```

Set `CHROME_PATH` when running on a machine that has Chrome installed but does not have Playwright browser binaries:

```powershell
$env:CHROME_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
```
