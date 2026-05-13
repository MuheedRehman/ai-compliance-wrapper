# Dashboard E2E Testing

The dashboard has a Playwright product smoke suite that covers:

- API preflight checks for the core backend endpoints.
- Main navigation rendering and visible error detection.
- Critical create flows for systems, features, controls, intake, oversight, incidents, reports, and governed runtime.

Staging routes browser API calls through the dashboard server. The dashboard service reads `DASHBOARD_API_KEY` from Secret Manager and forwards requests to the backend without exposing the key in browser JavaScript. This keeps public staging easy to open, but it is not the production authentication model. Production should replace this with OAuth/JWT-backed user sessions.

## Local

Start the backend and dashboard, then run:

```powershell
$env:DASHBOARD_API_KEY = "<dashboard api key>"
$env:BACKEND_URL = "http://localhost:8000"
npm run e2e
```

If you want Playwright to start the dashboard dev server:

```powershell
$env:E2E_START_SERVER = "1"
$env:DASHBOARD_API_KEY = "<dashboard api key>"
$env:BACKEND_URL = "http://localhost:8000"
npm run e2e
```

## Staging

```powershell
$env:DASHBOARD_URL = "https://ai-compliance-dashboard-loilav7ubq-ey.a.run.app"
$env:BACKEND_URL = "https://ai-compliance-backend-loilav7ubq-ey.a.run.app"
$env:DASHBOARD_API_KEY = "<staging dashboard api key>"
npm run e2e:staging
```

Set `CHROME_PATH` when running on a machine that has Chrome installed but does not have Playwright browser binaries:

```powershell
$env:CHROME_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
```
