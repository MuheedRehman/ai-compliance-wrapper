# Work Tracker

Last updated: 2026-05-15

This is the working memory for the project. Update it whenever a module is started, completed, paused, or reprioritized.

## Current Position

We are working from:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI
```

Current product focus:

1. Build Module 4: Obligation Engine 2.0 from the EU AI Act best-practice blueprint.
2. Keep Module 5 Evidence Vault connected to obligation evidence requirements.
3. Keep Module 3 AI System Lifecycle Workspace usable as the command center for each AI system.
4. Keep Module 1 scanner output tightly connected to obligation dimensions and each AI system workspace.
5. Keep Module 2 auth/tenant work stable because it is already started and security-critical.

Current technical baseline:

- Backend FastAPI app exists.
- Alembic migrations exist through `0009_evidence_vault_items.py`.
- Dashboard Next.js app exists under `backend/apps/dashboard`.
- Tests exist for scanner, tenant admin, classification, obligation engine, controls, reports, billing, runtime, migrations, and feature lifecycle.
- Canonical Git/project root is the nested `backend` folder. The outer duplicate shell has been archived into `_archive_outer_duplicate_2026-05-14`, and the old outer Git repo has been archived into `_archive_outer_git_2026-05-14`.
- GitHub origin is `https://github.com/MuheedRehman/ai-compliance-wrapper.git`; `main` is the active branch.
- Latest deployed staging baseline: commit `c1d588c` via Cloud Build `3572a668-5d22-45be-aa80-101b99b4cc2c` with status `SUCCESS`.
- Live staging URLs:
  - Dashboard: `https://ai-compliance-dashboard-loilav7ubq-ey.a.run.app`
  - Backend: `https://ai-compliance-backend-loilav7ubq-ey.a.run.app`
- Latest verified Cloud Run revisions:
  - Dashboard: `ai-compliance-dashboard-00026-249`
  - Backend: `ai-compliance-backend-00049-5gr`

## Module Status Board

| Module | Status | Current State | Next Work |
| --- | --- | --- | --- |
| 1. Website / SaaS Compliance Scanner | In progress | Route, service, migration, tests, dashboard scanner pages, scan-to-system conversion, system-specific control materialization, signed conversion evidence, one-click compliance readiness report generation, and scanner-to-obligation dimension output exist. | Harden crawl/extraction quality, add deeper public-page evidence extraction, and polish report/audit pack output. |
| 2. Real Auth, Tenants, Users, Roles | In progress | Tenant users, invitations, auth policies, login audit, Google login resolution, dashboard settings page exist. | Verify role mapping, lock down staging assumptions, add/confirm audit coverage for important user actions. |
| 3. AI System Lifecycle Workspace | In progress | System workspace API and dashboard detail page now aggregate classification, features, controls, evidence, scans, reports, FRIA, oversight, and incidents around one AI system. | Add editable owners/deadlines/review history and deeper drill-down actions from each workspace section. |
| 4. Obligation Engine 2.0 | In progress | Structured compliance-dimension catalog, article/effective-date/scanner/evidence/control metadata, enriched intake obligation graphs, scanner-to-dimension scoring/output, `/v1/obligations/dimensions`, `/v1/obligations/explain/intake/{id}`, dashboard intake/scanner dimension display, and tests exist. | Add deeper Annex III subcategory mapping, provider/deployer obligation branching, and more effective-date/deadline automation. |
| 5. Evidence Vault | In progress | First-class signed evidence items now exist with source, owner, type, status, hash/signature, related control/system, review/expiry dates, API routes, dashboard vault UI, and AI system workspace linkage. | Add file/object storage, upload flows, artifact previews, and stronger evidence-to-control attachment workflows. |
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
- Deployment pipeline restored after UI/test wording drift: live scanner E2E now verifies the current `CREATE WORKSPACE` flow, GitHub is pushed, and GCP Cloud Build deploys backend/dashboard with live E2E passing.
- Module 5 first evidence vault slice completed locally: `/v1/evidence/items` and `/v1/evidence/summary` manage signed vault items, the dashboard Evidence page now combines vault items with immutable logs, and AI system workspaces count/show vault items.
- Evidence Vault dashboard form-control contrast fix deployed: global dark styling now covers inputs, selects, textareas, select options, and date picker icons.
- EU AI Act best practices captured for Module 4: structured compliance dimensions, scanner-to-obligation mapping, modular explainable rules, API/security tests, and live E2E pipeline requirements.
- Module 4 first obligation engine slice completed and deployed: structured EU AI Act dimensions now drive enriched intake obligation graphs, explanation output, controls/evidence requirements, and intake detail dashboard display.
- Module 4 scanner-to-obligation slice completed locally: website scan results now include applicable EU AI Act dimensions, legal basis, evidence requirements, mapping confidence, dimension-linked gap/action output, and scanner detail dashboard display.
- Module 2 started: tenant admin/auth policies/users/invitations/login audit/dashboard settings.
- Module 6 started: compliance controls/readiness scorecard.
- Module 8 started: report service and report pages.
- Runtime governance foundation exists from earlier sprints.

## Active Next Checklist

Use this as the next session checklist.

- [x] Run backend test suite from `backend`.
- [x] Confirm Alembic head is `0009_evidence_vault_items.py`.
- [x] Validate Module 1 scanner happy path in API and dashboard.
- [ ] Improve scanner extraction/gap output if results are shallow.
- [x] Make "convert scan" create or update a useful AI system profile.
- [x] Connect scanner result to controls/evidence/report generation.
- [x] Decide whether to finish Module 1 before further Module 2 hardening. Decision: move into Module 3 while preserving Module 1 links.
- [x] Commit roadmap/tracker/cleanup docs inside the canonical `backend` repo.
- [x] Clean up or archive the misleading outer duplicate shell after approval.
- [x] Commit and push the recovery/module baseline to GitHub.
- [x] Deploy latest pushed baseline to GCP staging and verify live dashboard response.
- [x] Start Module 5 Evidence Vault first-class evidence item model and workflow.
- [x] Deploy Module 5 Evidence Vault slice to GCP staging and update the deployed baseline.
- [x] Capture EU AI Act best practices as Module 4 blueprint and coverage acceptance criteria.
- [x] Implement Module 4 structured obligation dimensions from the blueprint.
- [x] Deploy Module 4 first obligation engine slice to GCP staging and update the deployed baseline.
- [x] Implement scanner-to-obligation dimension mapping and dashboard display.
- [ ] Deploy scanner-to-obligation dimension mapping to GCP staging and update the deployed baseline.

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
