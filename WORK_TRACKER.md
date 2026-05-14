# Work Tracker

Last updated: 2026-05-14

This is the working memory for the project. Update it whenever a module is started, completed, paused, or reprioritized.

## Current Position

We are working from:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI
```

Current product focus:

1. Build Module 3: AI System Lifecycle Workspace.
2. Keep Module 1 scanner output tightly connected to each AI system workspace.
3. Keep Module 2 auth/tenant work stable because it is already started and security-critical.

Current technical baseline:

- Backend FastAPI app exists.
- Alembic migrations exist through `0008_tenant_user_admin.py`.
- Dashboard Next.js app exists under `backend/apps/dashboard`.
- Tests exist for scanner, tenant admin, classification, controls, reports, billing, runtime, migrations, and feature lifecycle.
- Canonical Git/project root is the nested `backend` folder. The outer duplicate shell has been archived into `_archive_outer_duplicate_2026-05-14`, and the old outer Git repo has been archived into `_archive_outer_git_2026-05-14`.

## Module Status Board

| Module | Status | Current State | Next Work |
| --- | --- | --- | --- |
| 1. Website / SaaS Compliance Scanner | In progress | Route, service, migration, tests, dashboard scanner pages, scan-to-system conversion, system-specific control materialization, signed conversion evidence, and one-click compliance readiness report generation exist. | Harden crawl/extraction quality, improve gap detection, and polish report/audit pack output. |
| 2. Real Auth, Tenants, Users, Roles | In progress | Tenant users, invitations, auth policies, login audit, Google login resolution, dashboard settings page exist. | Verify role mapping, lock down staging assumptions, add/confirm audit coverage for important user actions. |
| 3. AI System Lifecycle Workspace | In progress | System workspace API and dashboard detail page now aggregate classification, features, controls, evidence, scans, reports, FRIA, oversight, and incidents around one AI system. | Add editable owners/deadlines/review history and deeper drill-down actions from each workspace section. |
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
- Module 1 workspace starter slice completed: converting a scan now creates/links an AI system, intake, obligation-derived controls, and a signed evidence log; scanner detail links to system controls and evidence.
- Module 1 one-click report slice completed: scanner reports now convert the scan if needed, preserve scan/intake/evidence source references, and generate a compliance readiness report from the scanner detail page.
- Module 3 first workspace slice completed: `/v1/ai-systems/{id}/workspace` aggregates lifecycle records, and the AI system detail dashboard now presents readiness, classification, controls, evidence, scans, reports, governance records, and features in one workspace.
- Module 2 started: tenant admin/auth policies/users/invitations/login audit/dashboard settings.
- Module 6 started: compliance controls/readiness scorecard.
- Module 8 started: report service and report pages.
- Runtime governance foundation exists from earlier sprints.

## Active Next Checklist

Use this as the next session checklist.

- [x] Run backend test suite from `backend`.
- [x] Confirm Alembic head is `0008_tenant_user_admin.py`.
- [x] Validate Module 1 scanner happy path in API and dashboard.
- [ ] Improve scanner extraction/gap output if results are shallow.
- [x] Make "convert scan" create or update a useful AI system profile.
- [x] Connect scanner result to controls/evidence/report generation.
- [x] Decide whether to finish Module 1 before further Module 2 hardening. Decision: move into Module 3 while preserving Module 1 links.
- [x] Commit roadmap/tracker/cleanup docs inside the canonical `backend` repo.
- [x] Clean up or archive the misleading outer duplicate shell after approval.
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
