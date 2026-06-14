# Work Tracker

Last updated: 2026-06-14

This is the working memory for the project. Update it whenever a module is started, completed, paused, or reprioritized.

## Current Position

We are working from:

```text
D:\AI_Compliance\Backend\Sprint6B_Migrations_Postgres_CI
```

Current product focus:

1. Module 7 FRIA Builder: implemented and locally verified; deploy to staging next.
2. Module 2 hardening: add backend route-level permission checks beyond the dashboard proxy.
3. Module 8 Report Builder: add PDF export, evidence bundle, AI system factsheet.
4. Module 5 Evidence Vault: move artifact storage from database bytes to GCS.

Current module slice:

- Module 7 FRIA Builder: guided 6-section wizard, section-level save with completion tracking, submit-for-review (draft → in_review), approve/reject workflow (in_review → approved/rejected), Markdown export, and full dashboard wizard are implemented. Migration 0013 adds sections_json, approval_json, completion_percent. Local verification passed: full backend test suite and dashboard lint/build. Pending Cloud Build deploy.

## Mandatory Module Execution Workflow

When the user asks to continue, carry on, execute, or implement any module slice, the default workflow is end-to-end:

1. Read `WORK_TRACKER.md`, read `MODULE_ROADMAP_RECOVERY.md`, and run `git status --short --branch`.
2. Continue from the latest deployed staging baseline recorded in this tracker.
3. Implement the requested slice locally with scoped tests and UI checks where applicable.
4. Run the relevant test suite; for deployable slices, run the full backend suite and dashboard lint/build checks when frontend code changed.
5. Update `WORK_TRACKER.md` and any relevant roadmap/docs.
6. Commit all intended changes in the canonical nested `backend` repo.
7. Push the commit to GitHub `main`.
8. Deploy the pushed commit to GCP staging through Cloud Build.
9. Verify the live Cloud Run backend/dashboard revisions and live smoke/E2E result.
10. Update this tracker with the new deployed commit, Cloud Build id/status, Cloud Run revisions, and any verification notes.

Do not stop after local implementation unless the user explicitly asks for local-only work or deployment is blocked by credentials, infrastructure, or a failing gate.

Current technical baseline:

- Backend FastAPI app exists.
- Alembic migrations exist through `0012_evidence_artifacts.py`.
- Dashboard Next.js app exists under `backend/apps/dashboard`.
- Tests exist for scanner, tenant admin, classification, obligation engine, controls, reports, billing, runtime, migrations, and feature lifecycle.
- Canonical Git/project root is the nested `backend` folder. The outer duplicate shell has been archived into `_archive_outer_duplicate_2026-05-14`, and the old outer Git repo has been archived into `_archive_outer_git_2026-05-14`.
- GitHub origin is `https://github.com/MuheedRehman/ai-compliance-wrapper.git`; `main` is the active branch.
- Latest deployed staging baseline: commit `ee94e0b` via Cloud Build `8d765362-9c39-46d8-8a29-b6898eddbb32` with status `SUCCESS`.
- Live staging URLs:
  - Dashboard: `https://ai-compliance-dashboard-loilav7ubq-ey.a.run.app`
  - Backend: `https://ai-compliance-backend-loilav7ubq-ey.a.run.app`
- Latest verified Cloud Run revisions:
  - Dashboard: `ai-compliance-dashboard-00052-h7w`
  - Backend: `ai-compliance-backend-00101-nsb`

## Module Status Board

| Module | Status | Current State | Next Work |
| --- | --- | --- | --- |
| 1. Website / SaaS Compliance Scanner | In progress | Route, service, migration, tests, dashboard scanner pages, scan-to-system conversion, system-specific control materialization, signed conversion evidence, transaction-safe one-click compliance readiness report generation, scanner-to-obligation dimension output, Annex III subcategory match output, penalty exposure on gaps/actions, role-based obligation scenarios, persisted role selection for conversion/report generation, broader compliance-page crawling, topic-level public evidence profiling, and a deployed Playwright smart-scroller rendered crawl implementation exist. | Add multilingual signal catalogs, rendered screenshot evidence, and scanner queue/progress UI if rendered scans become slow for larger SaaS sites. |
| 2. Real Auth, Tenants, Users, Roles | In progress | Tenant users, invitations, auth policies, login audit, admin action audit, Google/password login resolution, dashboard settings page, active-user-bound dashboard RBAC headers, production config guardrails, expanded tenant-role permissions, dashboard proxy permission enforcement for governance/billing/runtime/evidence/report/scanner actions, and role/access visibility in the UI exist. | Add backend route-level dashboard permission dependencies beyond the dashboard proxy and audit actor attribution for non-admin governance mutations. |
| 3. AI System Lifecycle Workspace | In progress | System workspace API and dashboard detail page now aggregate classification, features, controls, evidence, scans, reports, FRIA, oversight, incidents, editable owner/deadline metadata, lifecycle notes, deployed review-history events, deployed review follow-up tasks, deployed multi-action review plans with control/evidence placeholders, and deployed workspace drill-down actions around one AI system. | Continue polishing section-specific create/edit flows, or move to Module 5 evidence uploads. |
| 4. Obligation Engine 2.0 | In progress | Structured compliance-dimension catalog, Annex III subcategory catalog/matcher, EU AI Act penalty exposure catalog, article/effective-date/scanner/evidence/control metadata, enriched intake obligation graphs, scanner-to-dimension scoring/output, scanner provider/deployer/importer scenario branching, persisted scanner role-to-intake selection, `/v1/obligations/dimensions`, `/v1/obligations/annex-iii`, `/v1/obligations/penalties`, `/v1/obligations/explain/intake/{id}`, dashboard intake/scanner dimension display, and tests exist. | Add more effective-date/deadline automation and richer "because you answered X" explanations for scanner-created workspaces. |
| 5. Evidence Vault | In progress | First-class signed evidence items now exist with source, owner, type, status, hash/signature, related control/system, review/expiry dates, API routes, dashboard vault UI, AI system workspace linkage, deployed database-backed uploaded artifacts with artifact hashes/signatures and download endpoints, a deployed evidence-to-control attachment workflow, and a deployed artifact preview workflow. | Add an external object-storage backend. |
| 6. Control Management | In progress | Compliance controls, readiness scorecard, evidence coverage, evidence attachment, owner/status/due date editing, severity, review cadence, review history, review comments, reusable control templates, audit-status export, and a full-width template catalog UI are deployed to staging. | Add reusable-template customization and branded/exportable control status reports. |
| 7. FRIA / Risk Assessment Builder | In progress | Guided 6-section builder, section save, completion percent, submit-for-review, approve/reject, Markdown export, and full dashboard wizard now exist. | Add multi-reviewer approval chains, PDF export, and FRIA status in system workspace tiles. |
| 8. Report Builder / Audit Pack | Started | Report service and dashboard report pages exist; report JSON/Markdown now includes penalty exposure bands when controls are missing or incomplete, and scanner-generated reports now include a scanner audit pack with public evidence coverage, found/missing evidence topics, public source excerpts, scanner gap findings, and remediation actions. | Continue polished audit pack work: PDF, evidence bundle packaging, AI system factsheet, and richer remediation plan export. |
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
- Module 4 scanner-to-obligation slice completed and deployed: website scan results now include applicable EU AI Act dimensions, legal basis, evidence requirements, mapping confidence, dimension-linked gap/action output, and scanner detail dashboard display.
- Report detail hotfix deployed: scanner-generated reports now open without a client-side route-param crash, and report pages tolerate missing or older report JSON fields gracefully.
- Module 4 Annex III subcategory slice completed and deployed: official high-risk category catalog, `/v1/obligations/annex-iii`, text matcher, scanner `annex_iii_matches`, intake graph propagation, scanner dashboard display, and tests now exist.
- Module 4 penalty exposure slice completed and deployed: Article 99/101 fine bands now appear in obligation dimensions, scanner gaps/actions, controls, report JSON/Markdown, scanner/report dashboard pages, and `/v1/obligations/penalties`.
- Module 4 role-branching slice completed and deployed: each scanner result now includes Provider, Deployer, and Importer/Distributor obligation scenarios with role-specific dimensions, controls, evidence requirements, manual-review flags, and fine exposure.
- Module 4 role-selection slice completed and deployed: scanner users can choose Provider, Deployer, or Importer/Distributor before creating a workspace/report, and that chosen role now drives the created intake, controls, evidence scope, and persisted scan state.
- Backend hardening slice completed and deployed: scanner workspace/report creation now runs atomically with rollback coverage, shared creation services support caller-owned transactions, and production config rejects SQLite, weak evidence secrets, wildcard frontend CORS, demo AI mode, mock Stripe defaults, and missing live OpenAI credentials.
- Module 2 RBAC hardening slice completed and deployed: tenant-admin dashboard role headers must now match an active tenant user, tenant headers must match the API-key tenant, password login resolves through the backend before issuing a session cookie, and staging seed creates the password owner user.
- Module 2 action audit slice completed and deployed: tenant/user creation, role/status updates, invitation creation/revocation, and auth policy changes now create before/after admin audit events exposed through `/v1/tenant-admin/action-audit`, tenant summary, and the dashboard Users & Access page.
- Module 1 scanner extraction hardening completed and deployed: scanner crawl candidates now include trust center, security/compliance, DPA, subprocessors, docs, and help pages; public evidence profiling extracts disclosure, human oversight, logging/monitoring, limitations, data governance, security, and vendor-documentation evidence; source pages now include evidence topics; and high-risk gap output now flags missing disclosure, oversight, and logging/incident evidence more specifically.
- Module 8 scanner audit pack polish completed and deployed: scanner-generated compliance readiness reports now include a dedicated `scanner_audit_pack` in report JSON/Markdown with coverage score, found/missing public evidence topics, source excerpts, scanner-derived findings, remediation actions, and penalty exposure propagation; dashboard report detail now renders the scanner audit pack.
- Deployment workflow memory completed and pushed: `WORK_TRACKER.md` and `MODULE_ROADMAP_RECOVERY.md` now state that module work must be implemented, tested, committed, pushed, deployed to GCP staging, verified, and recorded unless explicitly local-only or blocked.
- Module 1 rendered SaaS crawl upgrade completed and deployed: design documented in `docs/rendered-scanner-crawl-plan.md`; scanner now has a hybrid raw HTML plus Playwright rendering strategy with app-shell detection, bounded smart scrolling, safe expansion clicks, extraction modes, render metadata, fallback gap reporting, Dockerized Chromium support, and backend Cloud Run memory increased to `1Gi` for rendered scans.
- Module 1 smart-scroller deployment note: initial Cloud Build `41c6e5e7-2807-47d1-b5b3-9c3e886261f4` deployed backend/dashboard but failed final live E2E because missing candidate pages such as guessed privacy/terms URLs were being rendered, making the live scanner path too slow. Follow-up commit `8cf3fcf` prevents rendering missing/404 candidate URLs, keeps rendering only for successfully fetched shallow JavaScript pages, adds regression coverage, and deployed successfully through Cloud Build `bcbd4add-0288-489c-9f14-958ccbad2cd0`.
- Module 3 lifecycle workspace operations completed and deployed: AI systems now support business/technical/legal owners, review status, next-review deadline, lifecycle notes, and a review event timeline through migration `0011`; `/v1/ai-systems/{id}/workspace` now returns governance summary and review metrics; dashboard system detail pages can update lifecycle metadata and record review checkpoints. Deployed through Cloud Build `1fab1f14-e234-4378-ba93-be62ba832ea3` to backend `ai-compliance-backend-00077-xrx` and dashboard `ai-compliance-dashboard-00040-h7d`.
- Module 3 review follow-up actions completed and deployed: review checkpoint actions now create AI-system-linked `review_tasks` with source review event, action index, target type, control/evidence target metadata, owner, due date, and severity; workspace responses now include follow-up task metrics and `follow_up_tasks`; the dashboard can record a follow-up while saving a review and close follow-up tasks from the system workspace. Deployed through Cloud Build `c113c92c-bde4-40a7-ad4d-29d29eca5e09` to backend `ai-compliance-backend-00079-xm6` and dashboard `ai-compliance-dashboard-00041-xz2`.
- Module 3 multi-action review plans completed and deployed: the AI system review checkpoint UI can create up to five follow-up actions; backend review actions can create linked placeholder compliance controls or signed evidence items when target type is Control or Evidence; review tasks store the created placeholder ID/type, owner, due date, severity, and source review event; workspace follow-up cards show created placeholder/owner/due metadata. Deployed through Cloud Build `ae655071-d756-4fe7-85cd-7ee2175c8779` to backend `ai-compliance-backend-00081-n6k` and dashboard `ai-compliance-dashboard-00042-6sv`; Cloud Build staging Playwright E2E passed.
- Module 3 workspace drill-down actions completed and deployed: `/v1/ai-systems/{id}/workspace` now returns `drill_down_actions` for controls, evidence, reports, FRIA, oversight, incidents, and follow-up tasks; the system workspace has action tiles to seed controls, open/prefill evidence, generate readiness reports, start/open FRIA drafts, assign oversight, and report incidents; target pages now honor `ai_system_id` context for scoped lists and prefilled create forms. Deployed through Cloud Build `9f80eded-091c-4d76-8fdd-64fb76e06cd5` to backend `ai-compliance-backend-00083-td5` and dashboard `ai-compliance-dashboard-00043-6gj`; Cloud Build staging Playwright E2E passed.
- Module 5 evidence upload flow completed and deployed: migration `0012` adds `evidence_artifacts`; `/v1/evidence/items/{item_id}/artifacts` accepts file uploads up to 5 MB and stores content in the database-backed artifact store with SHA-256 artifact hash and HMAC signature; `/download` streams the artifact with hash/signature headers; evidence item metadata and evidence hash are resealed after upload; the Evidence Vault dashboard can attach a file while creating evidence, upload files to existing items, and download uploaded artifacts. Deployed through Cloud Build `470a39b9-0dbf-44f6-9236-3dd5e40dba18` to backend `ai-compliance-backend-00085-rsx` and dashboard `ai-compliance-dashboard-00044-cw5`; Cloud Build staging Playwright E2E passed.
- Module 5 evidence-to-control attachment workflow completed and deployed: `/v1/compliance/controls` responses now include evidence coverage counts/statuses/latest evidence date; `/v1/compliance/controls/{control_id}/evidence` lists control evidence; `/v1/compliance/controls/{control_id}/evidence/{item_id}` attaches an existing evidence item to a control, inherits the control AI system when needed, records attachment metadata, and reseals the evidence hash. The Controls dashboard now shows evidence coverage, creates evidence prefilled for a selected control, and attaches existing evidence; the Evidence dashboard honors `control_id` filters. Initial Cloud Build `a8e12c87-93a2-4554-8d63-f972ba11dd9a` deployed backend/dashboard but failed the final live E2E gate because the new attachment select changed an existing broad control-status selector. Follow-up commit `48f70e5` added an explicit status select label and fixed the live E2E selector, then deployed successfully through Cloud Build `9711fd2d-227e-420e-b754-75dbd1c0eb3f` to backend `ai-compliance-backend-00089-xkd` and dashboard `ai-compliance-dashboard-00046-vwp`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 5 artifact preview workflow completed and deployed: `/v1/evidence/items/{item_id}/artifacts/{artifact_id}/preview` streams safe previewable artifacts inline with `no-store`, `nosniff`, artifact hash, and artifact signature headers; supported types include `text/*`, JSON, XML, CSV, Markdown, PDF, and images, while unsupported binary artifacts return `415` and remain download-only. The Evidence Vault dashboard now shows a Preview button for supported uploaded artifacts and renders text, image, and PDF previews in a closeable audit panel with file name, content type, size, and hash context. Deployed through Cloud Build `ff197d4a-42e7-4906-8756-e1057e9ae94d` to backend `ai-compliance-backend-00091-vkw` and dashboard `ai-compliance-dashboard-00047-thx`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 6 control lifecycle operations completed and deployed: control responses now expose severity, evidence-required/evidence-complete, review cadence, last/next review timestamps, review-overdue status, review history, and latest comments from existing control metadata; `/v1/compliance/controls/{control_id}/reviews` records review notes/history and can update status/severity/cadence; the Controls dashboard can edit owner/status/due date/severity/review cadence and record review notes inline. Local verification passed: `tests/test_compliance_controls.py`, full backend `tests`, dashboard lint, and dashboard build. Deployed through Cloud Build `60776990-d787-4535-8db6-60e49b9f7ec6` to backend `ai-compliance-backend-00093-ljz` and dashboard `ai-compliance-dashboard-00048-928`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 6 control template and audit-status export completed and deployed: `/v1/compliance/control-templates` lists reusable EU AI Act templates with applied-state metadata; `/v1/compliance/controls/apply-templates` materializes selected templates into tenant or AI-system scopes; `/v1/compliance/audit-status` returns control readiness summary, evidence/owner/deadline/review gaps, row-level audit readiness, and Markdown export content; the Controls dashboard can apply templates and download the Markdown audit status snapshot. Local verification passed: `tests/test_compliance_controls.py`, full backend `tests`, dashboard lint, and dashboard build. Deployed through Cloud Build `47502b9a-2591-41cc-b718-7e84edd2af40` to backend `ai-compliance-backend-00095-9q7` and dashboard `ai-compliance-dashboard-00049-5nw`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 6 control template UI polish completed and deployed: the Controls dashboard replaces the cramped half-width template dropdown with a full-width template catalog, visible Apply buttons on every template row, suggested evidence metadata, shared owner/due-date defaults, and E2E guardrails so health-check button sweeping does not apply templates accidentally. Local verification passed: full backend `tests`, dashboard lint, and dashboard build. Deployed through Cloud Build `3e1f3083-237b-4a18-bbc3-6472cfa6fb91` to backend `ai-compliance-backend-00097-zrb` and dashboard `ai-compliance-dashboard-00050-gvx`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 7 FRIA builder slice completed and deployed: migration `0013` adds sections_json/approval_json/completion_percent to fria_records; new endpoints `/sections`, `/submit`, `/review`, `/export`; guided 6-section dashboard wizard with completion bar, section tabs, save-per-section, submit/approve/reject modals, and Markdown export. Deployed through Cloud Build `8d765362-9c39-46d8-8a29-b6898eddbb32` to backend `ai-compliance-backend-00101-nsb` and dashboard `ai-compliance-dashboard-00052-h7w`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 2 customer-ready session and role enforcement completed and deployed: tenant roles now resolve to an explicit permission matrix; `/api/auth/me` exposes permissions and access labels; the dashboard proxy denies disallowed backend actions by method/path before they reach the API; the sidebar shows the active role/access level and hides billing/runtime links when the session lacks permission; Users & Access uses returned permissions to disable user/policy writes for non-admin roles. Local verification passed: `tests/test_tenant_admin.py`, full backend `tests`, dashboard lint, and dashboard build. Deployed through Cloud Build `900d712d-fe26-4b47-ab1f-037b22df2282` to backend `ai-compliance-backend-00099-g8j` and dashboard `ai-compliance-dashboard-00051-pdj`; Cloud Build staging Playwright E2E passed and dashboard `/login` returned `200 OK`.
- Module 2 started: tenant admin/auth policies/users/invitations/login audit/dashboard settings.
- Module 6 started: compliance controls/readiness scorecard.
- Module 8 started: report service and report pages.
- Runtime governance foundation exists from earlier sprints.

## Active Next Checklist

Use this as the next session checklist.

- [x] Run backend test suite from `backend`.
- [x] Confirm Alembic head is `0010_tenant_action_audit.py`.
- [x] Validate Module 1 scanner happy path in API and dashboard.
- [x] Improve scanner extraction/gap output if results are shallow.
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
- [x] Deploy scanner-to-obligation dimension mapping to GCP staging and update the deployed baseline.
- [x] Implement Annex III subcategory catalog, matcher, scanner output, and dashboard display.
- [x] Deploy Annex III subcategory mapping to GCP staging and update the deployed baseline.
- [x] Implement penalty exposure mapping for missing EU AI Act obligations.
- [x] Deploy penalty exposure mapping to GCP staging and update the deployed baseline.
- [x] Implement scanner provider/deployer/importer role scenario branching.
- [x] Deploy scanner role scenario branching to GCP staging and update the deployed baseline.
- [x] Implement scanner role scenario choice as a persisted intake/report option.
- [x] Deploy scanner role scenario choice to GCP staging and update the deployed baseline.
- [x] Implement backend hardening for scanner report transaction rollback and production config guardrails.
- [x] Deploy backend hardening slice to GCP staging and update the deployed baseline.
- [x] Implement Module 2 active-user-bound dashboard RBAC headers for tenant admin.
- [x] Deploy Module 2 RBAC hardening slice to GCP staging and update the deployed baseline.
- [x] Implement Module 2 admin action audit trail for tenant/user changes.
- [x] Deploy Module 2 admin action audit trail to GCP staging and update the deployed baseline.
- [x] Implement Module 8 scanner audit pack polish for scanner-generated reports.
- [x] Deploy Module 8 scanner audit pack polish to GCP staging and update the deployed baseline.
- [x] Document Module 1 rendered SaaS crawl upgrade design for future sessions.
- [x] Implement Module 1 Playwright smart-scroller rendered crawl upgrade.
- [x] Deploy Module 1 Playwright smart-scroller upgrade to GCP staging and update the deployed baseline.
- [x] Implement Module 3 lifecycle owner/deadline/review-history workspace slice.
- [x] Deploy Module 3 lifecycle owner/deadline/review-history workspace slice to GCP staging and update the deployed baseline.
- [x] Implement Module 3 review follow-up actions linked to controls/evidence tasks.
- [x] Deploy Module 3 review follow-up actions to GCP staging and update the deployed baseline.
- [x] Implement Module 3 multi-action review plans with control/evidence placeholders.
- [x] Deploy Module 3 multi-action review plans to GCP staging and update the deployed baseline.
- [x] Implement Module 3 workspace drill-down actions from each workspace section.
- [x] Deploy Module 3 workspace drill-down actions to GCP staging and update the deployed baseline.
- [x] Implement Module 5 Evidence Vault upload flow with signed artifacts.
- [x] Deploy Module 5 Evidence Vault upload flow to GCP staging and update the deployed baseline.
- [x] Implement Module 5 evidence-to-control attachment workflow.
- [x] Deploy Module 5 evidence-to-control attachment workflow to GCP staging and update the deployed baseline.
- [x] Implement Module 5 artifact preview workflow.
- [x] Deploy Module 5 artifact preview workflow to GCP staging and update the deployed baseline.
- [x] Implement Module 6 control lifecycle operations.
- [x] Deploy Module 6 control lifecycle operations to GCP staging and update the deployed baseline.
- [x] Implement Module 6 control templates and audit-status export.
- [x] Deploy Module 6 control templates and audit-status export to GCP staging and update the deployed baseline.
- [x] Implement Module 6 control template catalog UI polish.
- [x] Deploy Module 6 control template catalog UI polish to GCP staging and update the deployed baseline.
- [x] Implement Module 2 customer-ready session and role enforcement.
- [x] Deploy Module 2 customer-ready session and role enforcement to GCP staging and update the deployed baseline.
- [x] Implement Module 7 FRIA builder guided workflow (sections, submit, approve/reject, export).
- [x] Deploy Module 7 FRIA builder to GCP staging and update the deployed baseline.

## Tracking Rules Going Forward

1. Update this file after every implementation session and again after deployment verification.
2. Add new completed files/routes/tests under the relevant module status.
3. Keep `MODULE_ROADMAP_RECOVERY.md` as the product roadmap.
4. Keep this file as the operational task board.
5. When a module moves status, update both the status board and active checklist.
6. Before starting a new module, record the reason in "Current Position".
7. Every module slice is expected to be committed, pushed, deployed to GCP staging, and verified unless explicitly marked local-only or blocked.

## Status Definitions

- Future: not started beyond incidental foundations.
- Foundation only: core primitives exist but no complete product workflow.
- Basic records only: data/endpoints exist, but the guided workflow is not built.
- Started: meaningful backend/frontend behavior exists.
- In progress: current active module.
- Complete for MVP: usable end-to-end for an early customer.
- Hardened: tested, documented, secure enough for staging/production use.
