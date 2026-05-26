# Module Roadmap Recovery

Recovered from repository state on 2026-05-14. The previous chat transcript is not available in this session, so this file captures the implementation trail from docs, migrations, routes, tests, and file timestamps.

Operational tracker: `WORK_TRACKER.md`.

## Operational Execution Rule

Module work is not considered complete when it is only implemented locally. For every module slice, use the mandatory workflow in `WORK_TRACKER.md`: implement, test, update tracker/docs, commit in the nested `backend` repo, push to GitHub `main`, deploy to GCP staging through Cloud Build, verify live Cloud Run/backend-dashboard behavior, and record the deployed baseline. Only skip push/deploy when the user explicitly requests local-only work or a deploy gate is blocked.

## Confirmed Completed Phases

- Phase 1: Core AI Registry & Evidence Base
- Phase 2: System-Centric Refactoring
- Phase 3: Runtime Evidence Linkage
- Phase 0A: Cloud Foundation

Source of truth: `PHASE_TRACKER.md`.

## Product Module Roadmap

### Module 1: Website / SaaS Compliance Scanner

User enters a SaaS website URL. The platform crawls public pages, privacy policy, terms, AI pages, docs, help center, and security pages.

Signals extracted:
- Does the product use AI?
- Is it chatbot, agent, recommender, scoring, hiring, biometric, synthetic media, GPAI, etc.?
- Does it disclose AI use?
- Are there privacy/security/compliance pages?
- Are human oversight, logging, appeals, incident reporting, or model limitations mentioned?

Outputs:
- Draft AI system profile
- Draft EU AI Act classification
- Missing disclosure/gap list
- Evidence links from crawled pages
- Confidence score
- Suggested controls
- One-click compliance report

Rendered SaaS crawl upgrade:
- Keep raw HTML fetch as the fast first pass.
- Detect shallow JavaScript app shells and script-heavy compliance pages.
- Use Playwright Chromium only for likely JS-dependent pages.
- Scroll in bounded steps until text/page height stop changing.
- Safely expand non-destructive "show more" and accordion-style controls.
- Record `extraction_mode` and `render_metadata` for each source page and evidence ref.
- Fall back to raw HTML with an explicit scanner limitation gap if rendering fails.

Technical design: `docs/rendered-scanner-crawl-plan.md`.

Status: in progress. Backend route, service, migration, tests, dashboard scanner pages, evidence profiling, scanner audit pack reports, rendered crawl design, and Playwright smart scrolling implementation are deployed to staging. Next scanner hardening should focus on multilingual signal catalogs, rendered screenshot evidence, and queue/progress UX for slower rendered scans.

### Module 2: Real Auth, Tenants, Users, Roles

Roles:
- Owner/Admin
- Compliance Manager
- Legal Reviewer
- Technical Owner
- Auditor
- Read-only Viewer

Core requirements:
- Login
- Organization/tenant isolation
- User invitations
- Role-based access
- Audit trail for user actions
- Remove public staging assumptions

Status: in progress. Tenant users, invitations, auth policies, login audit, admin action audit, Google/password login resolution, active-user-bound dashboard session headers, and dashboard user settings exist.

Current customer-ready session and role enforcement slice:
- Tenant roles resolve to an explicit permission matrix covering tenant administration, billing, governance, evidence, reports, scanner execution, and runtime execution.
- `/api/auth/me` exposes the signed session's role, permission list, and access label to the dashboard.
- The dashboard backend proxy checks the requested backend path and method against the active role before forwarding with the server API key.
- Owner/Admin keep full tenant/billing/write/runtime access; Reviewer keeps contributor access for governance/evidence/reports/scanner workflows; Auditor and Viewer are read-only for governance/evidence/reports.
- The sidebar shows the active role/access level and hides billing/runtime navigation when the role lacks permission.
- Users & Access disables user and auth-policy writes based on returned permissions, while backend tenant-admin checks still validate active tenant users.

Deployment checkpoint: local implementation is ready for verification and GCP staging deployment. Next Module 2 hardening should add backend route-level dashboard permission dependencies beyond the dashboard proxy and audit actor attribution for non-admin governance mutations.

### Module 3: AI System Lifecycle Workspace

Each AI system should have:
- Overview
- Risk classification
- Features
- Controls
- Evidence
- Incidents
- FRIA
- Reports
- Owners
- Deployment status
- Review history
- Deadlines

Status: in progress. Registry, features, controls, evidence, incidents, FRIA, reports, and lifecycle owner/review operations are being unified into the AI system detail workspace.

Current lifecycle workspace operations slice:
- AI systems carry business owner, technical owner, legal owner, review status, next-review deadline, last-reviewed timestamp, and lifecycle notes.
- Review-history events capture reviewer, review type, outcome, notes, findings, follow-up actions, and next-review date.
- `/v1/ai-systems/{id}/workspace` returns owner coverage, review deadline status, and review-event metrics.
- The dashboard system detail page lets users update lifecycle metadata and record review checkpoints from the workspace.

Deployment checkpoint: lifecycle owner/deadline/review-history implementation is deployed to staging. Next workspace hardening should connect review follow-up actions to controls/evidence tasks and add deeper drill-down actions from each workspace section.

Current review follow-up actions slice:
- Review checkpoint actions create AI-system-linked review tasks.
- Follow-up tasks preserve the source review event, action index, target type, target control/evidence IDs when provided, owner, due date, and severity.
- `/v1/ai-systems/{id}/workspace` includes follow-up task metrics and task records.
- The dashboard system detail page lets users add one follow-up while recording a review, open the target controls/evidence area, and close follow-up tasks from the workspace.

Deployment checkpoint: review follow-up actions are deployed to staging. Next workspace hardening should add multi-action review plans and more direct creation of controls/evidence placeholders from follow-up actions.

Current multi-action review plan slice:
- The dashboard review checkpoint can capture up to five follow-up actions in one review.
- Control-targeted follow-ups without an existing control create a placeholder compliance control linked to the AI system.
- Evidence-targeted follow-ups without an existing evidence item create a signed `needs_review` evidence placeholder linked to the AI system.
- Follow-up review tasks include created placeholder IDs, owner, due date, severity, and source review event metadata.

Deployment checkpoint: multi-action review plans are deployed to staging through Cloud Build `ae655071-d756-4fe7-85cd-7ee2175c8779`, with backend revision `ai-compliance-backend-00081-n6k`, dashboard revision `ai-compliance-dashboard-00042-6sv`, and passing Cloud Build staging Playwright E2E. Next workspace hardening should add deeper drill-down actions from each workspace section.

Current workspace drill-down actions slice:
- `/v1/ai-systems/{id}/workspace` returns `drill_down_actions` for controls, evidence, reports, FRIA, oversight, incidents, and follow-up tasks.
- The dashboard system workspace includes action tiles for seeding controls, opening or creating evidence, generating a readiness report, starting or opening FRIA, assigning oversight, and reporting incidents.
- Evidence, reports, FRIA, oversight, incidents, and review task pages honor `ai_system_id` context for scoped lists and prefilled create flows where applicable.

Deployment checkpoint: workspace drill-down actions are deployed to staging through Cloud Build `9f80eded-091c-4d76-8fdd-64fb76e06cd5`, with backend revision `ai-compliance-backend-00083-td5`, dashboard revision `ai-compliance-dashboard-00043-6gj`, and passing Cloud Build staging Playwright E2E. Next workspace polish can deepen section-specific create/edit flows, or the product can move to Module 5 evidence uploads.

### Module 4: Obligation Engine 2.0

Add:
- EU AI Act article mapping
- Annex III category mapping
- Provider vs deployer obligations
- GPAI obligations
- Transparency obligations
- FRIA triggers
- Incident notification triggers
- Control requirements by risk class
- Effective date tracking

Target output: "Because you answered X, obligations A/B/C apply."

Best-practice implementation guide: `docs/obligation-engine-2-blueprint.md`.

Status: first slice implemented locally. Structured compliance dimensions now include pillar, article, Annex reference, actor role, trigger condition, scanner signals, required controls, required evidence, confidence policy, and effective dates. Intake records now produce enriched obligation graphs and an explanation endpoint.

### Module 5: Evidence Vault

Store and organize:
- Policies
- Screenshots
- Model cards
- DPIAs/FRIAs
- Risk assessments
- Human oversight docs
- Logs
- Incident records
- Vendor documentation
- Test results
- Generated reports

Each evidence item should have:
- Source
- Owner
- Timestamp
- Hash/signature
- Related control
- Related AI system
- Expiry/review date

Status: in progress. Signed evidence items, source/owner/type/status, related control/system, review/expiry dates, API routes, dashboard vault UI, and workspace linkage exist.

Current evidence upload flow slice:
- Migration `0012` adds `evidence_artifacts` linked to evidence items and tenants.
- Evidence artifacts store uploaded file bytes in a database-backed object record for this staging slice, with file name, content type, size, storage key, SHA-256 artifact hash, and HMAC signature.
- Uploading an artifact reseals the parent evidence item metadata/hash so audit records reflect attached files.
- The Evidence Vault API supports artifact upload and authenticated artifact download.
- The Evidence Vault dashboard supports attaching a file while creating evidence, uploading files onto existing items, and downloading attached artifacts.

Deployment checkpoint: evidence upload flow is deployed to staging through Cloud Build `470a39b9-0dbf-44f6-9236-3dd5e40dba18`, with backend revision `ai-compliance-backend-00085-rsx`, dashboard revision `ai-compliance-dashboard-00044-cw5`, and passing Cloud Build staging Playwright E2E. Next evidence hardening should add artifact previews, external object-storage backend, and stronger evidence-to-control attachment workflows.

Current evidence-to-control attachment slice:
- Compliance control responses include evidence coverage fields: linked evidence count, active evidence count, needs-review count, latest evidence date, and status counts.
- `/v1/compliance/controls/{control_id}/evidence` lists evidence linked to one control.
- `/v1/compliance/controls/{control_id}/evidence/{item_id}` links an existing evidence item to a control, inherits the control AI system where needed, records attachment metadata, and reseals the evidence hash/signature.
- The Controls dashboard shows evidence coverage per control, opens prefilled evidence creation for that control, and can attach existing eligible evidence items.
- The Evidence dashboard honors `control_id` query filters and keeps control/system context when creating evidence from a control.

Deployment checkpoint: evidence-to-control attachment is deployed to staging through Cloud Build `9711fd2d-227e-420e-b754-75dbd1c0eb3f`, with backend revision `ai-compliance-backend-00089-xkd`, dashboard revision `ai-compliance-dashboard-00046-vwp`, and passing Cloud Build staging Playwright E2E. Initial Cloud Build `a8e12c87-93a2-4554-8d63-f972ba11dd9a` reached deployment but failed final E2E because the new attachment select changed a broad control-status selector; follow-up commit `48f70e5` fixed the selector.

Current artifact preview slice:
- `/v1/evidence/items/{item_id}/artifacts/{artifact_id}/preview` streams previewable artifact bytes inline behind `evidence:read` authentication.
- Preview responses carry `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, artifact hash, and artifact signature headers.
- Previewable types include `text/*`, JSON, XML, CSV, Markdown, PDF, and images.
- Unsupported binary types return `415` and stay download-only.
- The Evidence Vault dashboard shows a Preview button only for previewable uploaded artifacts and renders text, image, and PDF content in a closeable audit preview panel with file metadata and hash context.

Deployment checkpoint: artifact previews are deployed to staging through Cloud Build `ff197d4a-42e7-4906-8756-e1057e9ae94d`, with backend revision `ai-compliance-backend-00091-vkw`, dashboard revision `ai-compliance-dashboard-00047-thx`, and passing Cloud Build staging Playwright E2E.

### Module 6: Control Management

Add:
- Control templates
- Assign owner
- Status
- Due date
- Evidence attachment
- Review cycle
- Comments
- Risk severity
- Exportable audit status

Example controls:
- Human oversight implemented
- Logging enabled
- User disclosure present
- Bias testing performed
- Incident process documented
- Data governance reviewed
- Model limitations documented

Status: in progress. Compliance controls, readiness scorecard, evidence coverage, evidence attachment, operational lifecycle fields, reusable templates, audit-status export, and a full-width template catalog UI are deployed to staging.

Current control lifecycle operations slice:
- Control API responses expose severity, evidence-required/evidence-complete, review cadence, last/next review timestamps, review-overdue status, review history, and latest comments from existing control metadata.
- `PATCH /v1/compliance/controls/{control_id}` can update owner, status, due date, severity, review cadence, and next review date.
- `POST /v1/compliance/controls/{control_id}/reviews` records review notes/history, latest comment metadata, reviewer, outcome, and optional status/severity/cadence changes.
- The Controls dashboard can edit owner/status/due date/severity/review cadence and record review notes inline from the control register.

Deployment checkpoint: control lifecycle operations are deployed to staging through Cloud Build `60776990-d787-4535-8db6-60e49b9f7ec6`, with backend revision `ai-compliance-backend-00093-ljz`, dashboard revision `ai-compliance-dashboard-00048-928`, and passing Cloud Build staging Playwright E2E. Next control hardening should add reusable control templates and exportable audit status.

Current control templates and audit-status export slice:
- `/v1/compliance/control-templates` lists reusable EU AI Act control templates with article, evidence domain, severity, review cadence, suggested evidence, actor roles, risk tiers, and applied-state metadata.
- `/v1/compliance/controls/apply-templates` materializes selected templates into tenant-wide or AI-system-specific control scopes while skipping existing controls.
- `/v1/compliance/audit-status` returns an exportable control readiness snapshot with evidence gaps, owner gaps, overdue controls, review-overdue controls, high-severity open controls, row-level audit readiness, and Markdown export content.
- The Controls dashboard can apply one reusable template at a time and download the Markdown audit status snapshot for the active scope.

Deployment checkpoint: template catalog and audit-status export are deployed to staging through Cloud Build `47502b9a-2591-41cc-b718-7e84edd2af40`, with backend revision `ai-compliance-backend-00095-9q7`, dashboard revision `ai-compliance-dashboard-00049-5nw`, and passing Cloud Build staging Playwright E2E. Next control hardening should add reusable-template customization and branded/exportable control status reports.

Current template catalog UI polish:
- The Controls dashboard template area is now full-width instead of sharing a cramped half-width row with audit export.
- Every template is visible as a row with title, article, severity, review cadence, suggested evidence, applied state, and its own Apply button.
- Owner and due-date defaults are shared above the catalog and used when applying any template.
- Live E2E health checks skip Apply buttons so page sweeps do not accidentally mutate control data.

Deployment checkpoint: template catalog UI polish is deployed to staging through Cloud Build `3e1f3083-237b-4a18-bbc3-6472cfa6fb91`, with backend revision `ai-compliance-backend-00097-zrb`, dashboard revision `ai-compliance-dashboard-00050-gvx`, and passing Cloud Build staging Playwright E2E.

### Module 7: FRIA / Risk Assessment Builder

Sections:
- Intended purpose
- Affected persons
- Fundamental rights risks
- Mitigation measures
- Human oversight
- Residual risk
- Approval workflow
- Exportable FRIA document

Status: basic FRIA records exist; builder workflow remains to build.

### Module 8: Report Builder / Audit Pack

Outputs:
- PDF compliance report
- Evidence bundle
- Control status report
- AI system factsheet
- Executive summary
- Gap assessment
- Remediation plan

Later: branded reports for paid customers.

Status: report service and report pages exist; polished audit pack/export workflow remains to build.

### Module 9: Runtime Governance SDK

Capabilities:
- Policy checks before model calls
- Evidence logging
- Feature-level approvals
- Block/allow decisions
- Prompt/output logging
- Incident triggers
- Model/provider abstraction
- Developer API keys
- Usage dashboard

Status: runtime governance foundation exists through the chat pipeline, feature approvals, evidence logging, and provider abstraction.

### Module 10: Integrations

Priority integrations:
- Google Drive / SharePoint for evidence
- Slack / Teams notifications
- Jira / Linear remediation tasks
- GitHub policy-as-code checks
- OpenAI / Azure OpenAI / Anthropic runtime governance
- GCP/Azure/AWS logs
- Stripe billing if SaaS monetization continues

Status: billing and provider foundations exist; broader integrations remain future work.

## Recommended Build Order

1. Website / SaaS Compliance Scanner
2. AI System Detail Workspace
3. Evidence Vault
4. Control Management Upgrade
5. Auth + Tenant/Roles Hardening
6. Obligation Engine 2.0
7. FRIA Builder
8. Report/Audit Pack
9. Runtime Governance SDK
10. Integrations + Billing polish

## Implemented Backend Modules

- Chat/runtime pipeline: `/v1/chat/completions`
- Features/versioning: `/v1/features`
- Evidence/logs: `/v1/logs`
- Review tasks: `/v1/review-tasks`
- AI system registry: `/v1/ai-systems`
- Billing and entitlements: `/v1/billing`, `/v1/webhooks/stripe`
- Classification/intake: `/v1/intake`
- Obligations: `/v1/obligations/fria`, `/v1/obligations/oversight`, `/v1/obligations/incidents`
- Reports: `/v1/reports`
- Compliance controls and readiness scorecard: `/v1/compliance`
- Website scanner: `/v1/website-scans`
- Tenant administration: `/v1/tenant-admin`

## Database Migration Trail

- `0001_initial_governance_schema.py`: initial governance schema
- `0002_postgres_partial_indexes.py`: PostgreSQL partial indexes
- `0003_ai_system_layer.py`: AI system layer
- `0004_billing_layer.py`: billing layer
- `0005_intake_layer.py`: intake/classification layer
- `0006_compliance_critical_patch.py`: compliance controls/reporting patch
- `0007_website_scanner.py`: website scan records
- `0008_tenant_user_admin.py`: tenant users, invitations, auth policies, login audit
- `0009_evidence_vault_items.py`: signed first-class evidence vault items

## May 13, 2026 Implementation Trail

- 00:28: dashboard systems/features page updates
- 00:42: report run form and report service updates
- 00:55: config and AI provider updates
- 14:36-14:49: dashboard package, Playwright config, app layout, icon, gitignore
- 15:54-16:02: website scanner migration, service, route, dashboard pages, and tests
- 16:44-16:50: dashboard logout/layout, Dockerfile, staging deployment docs, E2E docs
- 18:26-18:46: auth config route, Google OIDC helper, Terraform outputs/main updates
- 19:28-19:30: classification/control service updates, intake/control dashboard updates, classification tests
- 23:49: auth config and Google auth start route updates

## May 14, 2026 Early Implementation Trail

- 00:30-00:36: tenant admin models, migration `0008`, schemas, service, routes, tests, seed updates
- 00:37-00:42: dashboard server session, backend proxy, login/me/google callback routes, sidebar/status badge, settings/users page, live E2E updates
- 01:19: Cloud Build update

## Current Next Up

- Phase 0B: IAM & staging rollout verification
- Phase 4: Governance assessments, especially FRIA, oversight, and incident management hardening
- Practical next checkpoint: run release checks against SQLite and PostgreSQL, then decide whether to finish Tenant Admin/IAM polishing or move into deeper Phase 4 assessment workflows.
