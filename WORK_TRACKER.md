# Work Tracker

Last updated: 2026-05-14

This is the working memory for the project. Update it whenever a module is started, completed, paused, or reprioritized.

## Current Position

We are working from:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI
```

Current product focus:

1. Keep the EU AI Act best-practice blueprint as the acceptance standard for Module 4: Obligation Engine 2.0.
2. Move into Module 5: Evidence Vault as the current product slice.
2. Keep Module 3 AI System Lifecycle Workspace usable as the command center for each AI system.
3. Keep Module 1 scanner output tightly connected to each AI system workspace.
4. Keep Module 2 auth/tenant work stable because it is already started and security-critical.

Current technical baseline:

- Backend FastAPI app exists.
- Alembic migrations exist through `0009_evidence_vault_items.py`.
- Dashboard Next.js app exists under `backend/apps/dashboard`.
- Tests exist for scanner, tenant admin, classification, controls, reports, billing, runtime, migrations, and feature lifecycle.
- Canonical Git/project root is the nested `backend` folder. The outer duplicate shell has been archived into `_archive_outer_duplicate_2026-05-14`, and the old outer Git repo has been archived into `_archive_outer_git_2026-05-14`.
- GitHub origin is `https://github.com/MuheedRehman/ai-compliance-wrapper.git`; `main` is the active branch.
- Latest deployed staging baseline: commit `c285b61` via Cloud Build `ac44d91e-a03f-4e41-af5b-536a8edc4ee5` with status `SUCCESS`.
- Live staging URLs:
  - Dashboard: `https://ai-compliance-dashboard-loilav7ubq-ey.a.run.app`
  - Backend: `https://ai-compliance-backend-loilav7ubq-ey.a.run.app`
- Latest verified Cloud Run revisions:
  - Dashboard: `ai-compliance-dashboard-00024-kkf`
  - Backend: `ai-compliance-backend-00045-gqh`

## Module Status Board

| Module | Status | Current State | Next Work |
| --- | --- | --- | --- |
| 1. Website / SaaS Compliance Scanner | In progress | Route, service, migration, tests, dashboard scanner pages, scan-to-system conversion, system-specific control materialization, signed conversion evidence, and one-click compliance readiness report generation exist. | Harden crawl/extraction quality, improve gap detection, and polish report/audit pack output. |
| 2. Real Auth, Tenants, Users, Roles | In progress | Tenant users, invitations, auth policies, login audit, Google login resolution, dashboard settings page exist. | Verify role mapping, lock down staging assumptions, add/confirm audit coverage for important user actions. |
| 3. AI System Lifecycle Workspace | In progress | System workspace API and dashboard detail page now aggregate classification, features, controls, evidence, scans, reports, FRIA, oversight, and incidents around one AI system. | Add editable owners/deadlines/review history and deeper drill-down actions from each workspace section. |
| 4. Obligation Engine 2.0 | Foundation only | Intake classification and obligation paths exist. Best-practice blueprint is captured in `docs/obligation-engine-2-blueprint.md`, and coverage gaps are tracked in `docs/compliance-coverage-matrix.md`. | Add structured compliance-dimension rules with article mapping, Annex III categories, actor roles, effective dates, scanner signals, evidence requirements, and explainable "because X, obligations Y apply" output. |
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
- EU AI Act best practices captured for Module 4: structured compliance dimensions, scanner-to-obligation mapping, modular explainable rules, API/security tests, and live E2E pipeline requirements.
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
- [x] Commit and push the recovery/module baseline to GitHub.
- [x] Deploy latest pushed baseline to GCP staging and verify live dashboard response.
- [x] Start Module 5 Evidence Vault first-class evidence item model and workflow.
- [x] Deploy Module 5 Evidence Vault slice to GCP staging and update the deployed baseline.
- [x] Capture EU AI Act best practices as Module 4 blueprint and coverage acceptance criteria.
- [ ] Implement Module 4 structured obligation dimensions from the blueprint.

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
