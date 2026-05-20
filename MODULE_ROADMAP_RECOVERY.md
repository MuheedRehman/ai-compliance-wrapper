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

Status: started. Tenant users, invitations, auth policies, login audit, Google login resolution, and dashboard user settings exist.

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

Deployment checkpoint: multi-action review plan implementation exists locally and is the current deployment checkpoint.

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

Status: first slice deployed. Signed evidence items, source/owner/type/status, related control/system, review/expiry dates, API routes, dashboard vault UI, and workspace linkage exist. File/object storage and stronger evidence-to-control attachment remain to build.

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

Status: started. Compliance controls and readiness scorecard exist; operational control lifecycle needs upgrade.

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
