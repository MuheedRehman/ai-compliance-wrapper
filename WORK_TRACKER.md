# Work Tracker

Last updated: 2026-05-14

This is the working memory for the project. Update it whenever a module is started, completed, paused, or reprioritized.

## Current Position

We are working from:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI
```

Current product focus:

1. Finish and harden Module 1: Website / SaaS Compliance Scanner.
2. Connect scanner outputs into Module 3: AI System Lifecycle Workspace.
3. Keep Module 2 auth/tenant work stable because it is already started and security-critical.

Current technical baseline:

- Backend FastAPI app exists.
- Alembic migrations exist through `0008_tenant_user_admin.py`.
- Dashboard Next.js app exists under `backend/apps/dashboard`.
- Tests exist for scanner, tenant admin, classification, controls, reports, billing, runtime, migrations, and feature lifecycle.
- Canonical Git/project root is the nested `backend` folder. The outer `Sprint6B_Migrations_Postgres_CI` folder contains a misleading duplicate shell; cleanup plan lives in `REPO_CLEANUP_PLAN.md`.

## Module Status Board

| Module | Status | Current State | Next Work |
| --- | --- | --- | --- |
| 1. Website / SaaS Compliance Scanner | In progress | Route, service, migration, tests, and dashboard scanner pages exist. | Harden crawl/extraction quality, improve gap detection, create better scan-to-system/report workflow. |
| 2. Real Auth, Tenants, Users, Roles | In progress | Tenant users, invitations, auth policies, login audit, Google login resolution, dashboard settings page exist. | Verify role mapping, lock down staging assumptions, add/confirm audit coverage for important user actions. |
| 3. AI System Lifecycle Workspace | Partially started | AI system registry and separate pages for features, controls, evidence, incidents, FRIA, reports exist. | Build unified AI system detail workspace with tabs/sections for lifecycle records. |
| 4. Obligation Engine 2.0 | Foundation only | Intake classification and obligation paths exist. | Add article mapping, Annex III categories, effective dates, and explainable "because X, obligations Y apply" output. |
| 5. Evidence Vault | Foundation only | Evidence logging and linked evidence concepts exist. | Add first-class evidence items with source, owner, hash, related control/system, expiry/review date. |
| 6. Control Management | Started | Compliance controls and readiness scorecard exist. | Add templates, owners, due dates, evidence attachment, review cycle, comments, severity. |
| 7. FRIA / Risk Assessment Builder | Basic records only | FRIA endpoints/pages exist. | Build guided FRIA workflow, approval path, and exportable FRIA document. |
| 8. Report Builder / Audit Pack | Started | Report service and dashboard report pages exist. | Produce polished audit pack: PDF, evidence bundle, factsheet, gap assessment, remediation plan. |
| 9. Runtime Governance SDK | Foundation only | Chat pipeline, feature approvals, provider abstraction, evidence logging exist. | Package policy checks, developer API keys, usage dashboard, and SDK-style docs. |
| 10. Integrations | Future | Stripe billing/provider foundations exist. | Add Drive/SharePoint, Slack/Teams, Jira/Linear, GitHub, cloud logs after core workflows stabilize. |

## Implemented Since Recovery

Recovered from repo state:

- Phase 1: Core AI Registry & Evidence Base completed.
- Phase 2: System-Centric Refactoring completed.
- Phase 3: Runtime Evidence Linkage completed.
- Phase 0A: Cloud Foundation completed.
- Module 1 started: website scanner backend, migration, tests, dashboard pages.
- Module 2 started: tenant admin/auth policies/users/invitations/login audit/dashboard settings.
- Module 6 started: compliance controls/readiness scorecard.
- Module 8 started: report service and report pages.
- Runtime governance foundation exists from earlier sprints.

## Active Next Checklist

Use this as the next session checklist.

- [ ] Run backend test suite from `backend`.
- [ ] Confirm Alembic head is `0008_tenant_user_admin.py`.
- [ ] Validate Module 1 scanner happy path in API and dashboard.
- [ ] Improve scanner extraction/gap output if results are shallow.
- [ ] Make "convert scan" create or update a useful AI system profile.
- [ ] Connect scanner result to controls/evidence/report generation.
- [ ] Decide whether to finish Module 1 before further Module 2 hardening.
- [ ] Commit roadmap/tracker/cleanup docs inside the canonical `backend` repo.
- [ ] Clean up or archive the misleading outer duplicate shell after approval.
- [ ] Commit a baseline so repo history starts preserving work.

## Tracking Rules Going Forward

1. Update this file after every implementation session.
2. Add new completed files/routes/tests under the relevant module status.
3. Keep `MODULE_ROADMAP_RECOVERY.md` as the product roadmap.
4. Keep this file as the operational task board.
5. When a module moves status, update both the status board and active checklist.
6. Before starting a new module, record the reason in "Current Position".

## Status Definitions

- Future: not started beyond incidental foundations.
- Foundation only: core primitives exist but no complete product workflow.
- Basic records only: data/endpoints exist, but the guided workflow is not built.
- Started: meaningful backend/frontend behavior exists.
- In progress: current active module.
- Complete for MVP: usable end-to-end for an early customer.
- Hardened: tested, documented, secure enough for staging/production use.
